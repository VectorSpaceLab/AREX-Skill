import os
import random
import re
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')

import numpy as np
import argparse
import gradio as gr
os.environ["GRADIO_TEMP_DIR"] = os.path.join(os.getcwd(), 'tmp')
import copy
import time
from datetime import datetime
import hashlib
import shutil
import requests
from PIL import Image, ImageFile
from peft import PeftModel
import torch
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

ImageFile.LOAD_TRUNCATED_IMAGES = True

from demo_asset.assets.css_html_js import custom_css
from demo_asset.serve_utils import Stream, Iteratorize
from demo_asset.conversation import CONV_VISION_INTERN2
from demo_asset.download import download_image_thread
from gradio_demo.utils import get_stopping_criteria, set_random_seed

import json
from datetime import datetime


meta_instruction = """You are an AI assistant whose name is InternLM-XComposer (浦语·灵笔).
- InternLM-XComposer (浦语·灵笔) is a conversational language model that is developed by Shanghai AI Laboratory (上海人工智能实验室). It is designed to be helpful, honest, and harmless.
- InternLM-XComposer (浦语·灵笔) can understand and communicate fluently in the language chosen by the user such as English and 中文.
"""
chat_meta = """You are an AI assistant whose name is InternLM-XComposer (浦语·灵笔).
- InternLM-XComposer (浦语·灵笔) is a multi-modality conversational language model that is developed by Shanghai AI Laboratory (上海人工智能实验室). It is designed to be helpful, honest, and harmless.
- InternLM-XComposer (浦语·灵笔) can understand and communicate fluently in the language chosen by the user such as English and 中文.
- InternLM-XComposer (浦语·灵笔) is capable of comprehending and articulating responses effectively based on the provided image.
"""

caption_meta_instruction = """请严格按照示例的<input> <output>格式，根据给定的文章，给出适合在某一段后插入的图像对应的标题。"""


max_section = 60
chat_stream_output = True
article_stream_output = True


def get_urls(caption, exclude):
    headers = {'Content-Type': 'application/json'}
    json_data = {'caption': caption, 'exclude': exclude, 'need_idxs': True}
    response = requests.post('https://lingbi.openxlab.org.cn/image/similar',
                             headers=headers,
                             json=json_data)
    urls = response.json()['data']['image_urls']
    idx = response.json()['data']['indices']
    return urls, idx


class ImageGroup(object):
    def __init__(self, cap, paths, pts=0):
        #assert len(paths) == 1 or len(paths) == 4, f"ImageGroup only support 1 or 4 images, not {len(paths)} images"
        self.cap = cap
        self.paths = paths
        self.pts = pts

    def __str__(self):
        return f"cap: {self.cap}; paths:{self.paths}; pts:{self.pts}"


class ImageProcessor:
    def __init__(self, vis_processor = None):
        self.vis_processor = vis_processor

    def __call__(self, item):
        if isinstance(item, str):
            item = Image.open(item).convert('RGB')
        # return self.transform(item)
        item = R560_HD18_Identity_transform(item)
        item = self.vis_processor(item).unsqueeze(0).cuda()
        return item


def padding_336(b, R=336):
    width, height = b.size
    tar = int(np.ceil(height / R) * R)
    top_padding = int((tar - height) / 2)
    bottom_padding = tar - height - top_padding
    left_padding = 0
    right_padding = 0
    b = transforms.functional.pad(
        b, [left_padding, top_padding, right_padding, bottom_padding],
        fill=[255, 255, 255])

    return b


def R560_HD18_Identity_transform(img):
    width, height = img.size
    trans = False
    if width < height:
        img = img.transpose(Image.TRANSPOSE)
        trans = True
        width, height = img.size
    ratio = (width / height)
    scale = 1
    while scale * np.ceil(scale / ratio) <= 18:
        scale += 1
    scale -= 1

    scale_low = min(np.ceil(width * 1.5 / 560), scale)
    scale_up = min(np.ceil(width * 1.5 / 560), scale)
    import random
    scale = random.randrange(scale_low, scale_up + 1)

    new_w = int(scale * 560)
    new_h = int(new_w / ratio)

    img = transforms.functional.resize(
        img,
        [new_h, new_w],
    )
    img = padding_336(img, 560)
    width, height = img.size
    if trans:
        img = img.transpose(Image.TRANSPOSE)

    return img


class Database(object):
    def __init__(self):
        self.title = '###'
        self.hash_title = hashlib.sha256(self.title.encode()).hexdigest()

    def addtitle(self, title, hash_folder, params):
        self.title = title
        self.hash_folder = hash_folder
        time = datetime.now()
        self.folder = os.path.join('databases', time.strftime("%Y%m%d"), 'composition', self.hash_folder)
        if os.path.exists(self.folder):
            shutil.rmtree(self.folder)

        os.makedirs(self.folder)
        with open(os.path.join(self.folder, 'index.txt'), 'w') as fd:
            fd.write(self.title + '\n')
            fd.write(self.hash_title + '\n')
            fd.write(str(time) + '\n')
            for key, val in params.items():
                fd.write(f"{key}:{val}" + '\n')
            fd.write('\n')

    def prepare_save_article(self, text_imgs, src_folder, tgt_folder):
        save_text = ''
        for txt, img in text_imgs:
            save_text += txt + '\n'
            if img is not None:
                save_text += f'<div align="center"> <img src={os.path.basename(img.paths[img.pts])} width = 500/> </div>'
                path = os.path.join(src_folder, os.path.basename(img.paths[img.pts]))
                dst_path = os.path.join(tgt_folder, os.path.basename(img.paths[img.pts]))
                if not os.path.exists(dst_path):
                    if os.path.exists(path):
                        shutil.copy(path, tgt_folder)
                    else:
                        shutil.copy(img.paths[img.pts], tgt_folder)
        return save_text

    def addarticle(self, text_imgs):
        if len(text_imgs) > 0:
            images_folder = os.path.join(self.folder, 'images')
            os.makedirs(images_folder, exist_ok=True)

        save_text = self.prepare_save_article(text_imgs, os.path.join('articles', self.hash_folder), images_folder)

        with open(os.path.join(self.folder, 'generate.MD'), 'w') as f:
            f.writelines(save_text)

    def addedit(self, edit_type, inst_edit, text_imgs):
        timestamp = datetime.now()
        with open(os.path.join(self.folder, 'index.txt'), 'a+') as f:
            f.write(str(edit_type) + '\n')
            f.write(str(inst_edit) + '\n')
            f.write(str(timestamp) + '\n\n')

        save_text = self.prepare_save_article(text_imgs, os.path.join('articles', self.hash_folder), os.path.join(self.folder, 'images'))
        with open(os.path.join(self.folder, str(timestamp).replace(' ', '-') + '.MD'), 'w') as f:
            f.writelines(save_text)


class Demo_UI:
    def __init__(self, ckpt_path, num_gpus=1):
        self.ckpt_path = ckpt_path
        self.reset()

        tokenizer = AutoTokenizer.from_pretrained(self.ckpt_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.ckpt_path, device_map='cuda', trust_remote_code=True, torch_dtype=torch.bfloat16).eval()
        self.model.tokenizer = tokenizer

        self.vis_processor = ImageProcessor(self.model.vis_processor)
        # self.vis_processor = self.model.vis_processor

        stop_words_ids = [92397]
        #stop_words_ids = [92542]
        self.stopping_criteria = get_stopping_criteria(stop_words_ids)
        set_random_seed(1234)
        self.r2 = re.compile(r'<Seg[0-9]*>')
        self.withmeta = False
        self.database = Database()

    def reset(self):
        self.pt = 0
        self.img_pt = 0
        self.texts_imgs = []
        self.open_edit = False
        self.hash_folder = '12345'
        self.instruction = ''
        torch.cuda.empty_cache()

    def reset_components(self):
        return (gr.Markdown(visible=True, value=''),) + (gr.Markdown(visible=False, value=''),) * (max_section - 1) + (
                gr.Button(visible=False),) * max_section + (gr.Image(visible=False),) * max_section + (gr.Accordion(visible=False),) * max_section * 2

    def text2instruction(self, text):
        if self.withmeta:
            return f"[UNUSED_TOKEN_146]system\n{meta_instruction}[UNUSED_TOKEN_145]\n[UNUSED_TOKEN_146]user\n{text}[UNUSED_TOKEN_145]\n[UNUSED_TOKEN_146]assistant\n"
        else:
            return f"[UNUSED_TOKEN_146]user\n{text}[UNUSED_TOKEN_145]\n[UNUSED_TOKEN_146]assistant\n"

    def text2instruction_caption(self, inst):
        return f"""[UNUSED_TOKEN_146]system\n{caption_meta_instruction}[UNUSED_TOKEN_145]\n[UNUSED_TOKEN_146]user\n<input>\n给定文章"<Seg0> 大多数的车友们在选车、购车时都会格外关注续航\n<Seg1> 甚至还有要求电动滑板车跑一百公里的\n<Seg2> 但这真的是你所需要的吗?\n<Seg3> 据报告，一线城市上班族通勤半径均在10公里以内\n<Seg4> 所以大多数通勤出行RND的续航完全可以满足\n<Seg5> 可能会有人说，续航短导致一天一充或两充很麻烦\n" 给出适合在<Seg4>后插入的图像对应的标题。</input>\n<output>\n标题是\"一个人正站在充电桩前给电动滑板车充电，面容看上去有些疲惫\"</output>\n<input>\n{inst}</input><output>[UNUSED_TOKEN_145]\n[UNUSED_TOKEN_146]assistant\n标题是\""""

    def get_images_xlab(self, caption, pt, exclude):
        urls, idxs = get_urls(caption.strip()[:53], exclude)
        print(urls[0])
        print('download image with url')
        download_image_thread(urls,
                              folder='articles/' + self.hash_folder,
                              index=pt,
                              num_processes=4)
        print('image downloaded')
        return idxs

    def generate(self, text, random, beam, max_length, repetition):
        with torch.no_grad():
            with torch.cuda.amp.autocast():
                input_ids = self.model.tokenizer(text, return_tensors="pt")['input_ids']
                len_input_tokens = len(input_ids[0])

                generate = self.model.generate(input_ids.cuda(),
                                                do_sample=random,
                                                num_beams=beam,
                                                temperature=1.,
                                                repetition_penalty=float(repetition),
                                                stopping_criteria=self.stopping_criteria,
                                                max_new_tokens=max_length,
                                                top_p=0.8,
                                                top_k=40,
                                                length_penalty=1.0,
                                                infer_mode='write',)
        response = generate[0].tolist()
        response = response[len_input_tokens:]
        response = self.model.tokenizer.decode(response, skip_special_tokens=True)
        response = response.replace('[UNUSED_TOKEN_145]', '')
        response = response.replace('[UNUSED_TOKEN_146]', '')
        return response

    def generate_with_emb(self, emb, random, beam, max_length, repetition, im_mask=None):
        with torch.no_grad():
            with torch.cuda.amp.autocast():
                generate = self.model.generate(inputs_embeds=emb,
                                                do_sample=random,
                                                num_beams=beam,
                                                temperature=1.,
                                                repetition_penalty=float(repetition),
                                                stopping_criteria=self.stopping_criteria,
                                                max_new_tokens=max_length,
                                                top_p=0.8,
                                                top_k=40,
                                                length_penalty=1.0,
                                                im_mask=im_mask,
                                                infer_mode='write',)
        response = generate[0].tolist()
        response = self.model.tokenizer.decode(response, skip_special_tokens=True)
        response = response.replace('[UNUSED_TOKEN_145]', '')
        response = response.replace('[UNUSED_TOKEN_146]', '')
        return response

    def extract_imgfeat(self, img_paths):
        if len(img_paths) == 0:
            return None
        images = []
        for j in range(len(img_paths)):
            image = self.vis_processor(img_paths[j])
            images.append(image)
        images = torch.stack(images, dim=0)
        with torch.no_grad():
            with torch.cuda.amp.autocast():
                img_embeds = self.model.encode_img(images)
        return img_embeds

    def generate_loc(self, text_sections, upimages, image_num):
        full_txt = ''.join(text_sections)
        input_text = '<image> ' * len(upimages) + f'给定文章"{full_txt}" 根据上述文章，选择适合插入图像的{image_num}行'
        instruction = self.text2instruction(input_text) + '适合插入图像的行是'
        print(instruction)

        if len(upimages) > 0:
            img_embeds = self.extract_imgfeat(upimages)
            input_embeds, im_mask, _ = self.interleav_wrap(instruction, img_embeds)
            output_text = self.generate_with_emb(input_embeds, True, 1, 200, 1.005, im_mask=im_mask)
        else:
            output_text = self.generate(instruction, True, 1, 200, 1.005)

        inject_text = '适合插入图像的行是' + output_text
        print(inject_text)

        locs = [int(m[4:-1]) for m in self.r2.findall(inject_text)]
        print(locs)
        return inject_text, locs

    def generate_cap(self, text_sections, pos, progress):
        pasts = ''
        caps = {}
        for idx, po in progress.tqdm(enumerate(pos), desc="image captioning"):
            full_txt = ''.join(text_sections[:po + 2])
            if idx > 0:
                past = pasts[:-2] + '。'
            else:
                past = pasts

            #input_text = f' <|User|>: 给定文章"{full_txt}" {past}给出适合在<Seg{po}>后插入的图像对应的标题。' + ' \n<TOKENS_UNUSED_0> <|Bot|>: 标题是"'
            input_text = f'给定文章"{full_txt}" {past}给出适合在<Seg{po}>后插入的图像对应的标题。'
            # instruction = self.text2instruction(input_text) + '标题是"'
            instruction = self.text2instruction_caption(input_text)
            print(instruction)
            cap_text = self.generate(instruction, True, 1, 200, 1.005)
            cap_text = '"'.join(cap_text.split('"')[:-1])
            # cap_text = cap_text.split('"')[0].strip()
            print(cap_text)
            caps[po] = cap_text

            if idx == 0:
                pasts = f'现在<Seg{po}>后插入图像对应的标题是"{cap_text}"， '
            else:
                pasts += f'<Seg{po}>后插入图像对应的标题是"{cap_text}"， '

        print(caps)
        return caps

    def interleav_wrap(self, text, image, max_length=16384):
        device = 'cuda'
        image_nums = len(image)
        parts = text.split('<image>')
        wrap_embeds, wrap_im_mask = [], []
        temp_len = 0
        need_bos = True

        for idx, part in enumerate(parts):
            if len(part) > 0:
                part_tokens = self.model.tokenizer(part,
                                                    return_tensors='pt',
                                                    padding='longest',
                                                    add_special_tokens=need_bos).to(device)
                if need_bos:
                    need_bos = False
                part_embeds = self.model.model.tok_embeddings(part_tokens.input_ids)
                wrap_embeds.append(part_embeds)
                wrap_im_mask.append(torch.zeros(part_embeds.shape[:2]))
                temp_len += part_embeds.shape[1]
            if idx < image_nums:
                wrap_embeds.append(image[idx])
                wrap_im_mask.append(torch.ones(1, image[idx].shape[1]))
                temp_len += image[idx].shape[1]

            if temp_len > max_length:
                break

        wrap_embeds = torch.cat(wrap_embeds, dim=1)
        wrap_im_mask = torch.cat(wrap_im_mask, dim=1)
        wrap_embeds = wrap_embeds[:, :max_length].to(device)
        wrap_im_mask = wrap_im_mask[:, :max_length].to(device).bool()
        return wrap_embeds, wrap_im_mask, temp_len

    def model_select_image(self, output_text, locs, images_paths, progress):
        print('model_select_image')
        pre_text = ''
        pre_img = []
        pre_text_list = []
        ans2idx = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        selected = {k: 0 for k in locs}
        for i, text in enumerate(output_text):
            pre_text += text + '\n'
            if i in locs:
                if len(pre_img) > 0:
                    pre_img = [i.detach() for i in pre_img]
                images = copy.deepcopy(pre_img)
                images = [i.cuda() for i in images]
                for j in range(len(images_paths[i])):
                    image = self.vis_processor(images_paths[i][j])
                    with torch.cuda.amp.autocast():
                        img_embeds = self.model.encode_img(image)
                    images.append(img_embeds)
                # images = torch.stack(images, dim=0)

                pre_text_list.append(pre_text)
                pre_text = ''

                # images = images.cuda()
                text = '根据给定上下文和候选图像，选择合适的配图：' + '<image>'.join(pre_text_list) + '候选图像包括: ' + '\n'.join([chr(ord('A') + j) + '.<image>' for j in range(len(images_paths[i]))])
                input_text = self.text2instruction(text) + '最合适的图是'
                print(input_text)
                with torch.no_grad():
                    with torch.cuda.amp.autocast():
                        # img_embeds = self.model.encode_img(images)
                        input_embeds, im_mask, len_input_tokens = self.interleav_wrap(input_text, images)

                with torch.no_grad():
                    with torch.cuda.amp.autocast():
                        outputs = self.model.generate(
                                            inputs_embeds=input_embeds,
                                            do_sample=True,
                                            temperature=1.,
                                            max_new_tokens=10,
                                            repetition_penalty=1.005,
                                            top_p=0.8,
                                            top_k=40,
                                            length_penalty=1.0,
                                            im_mask=im_mask,
                                            infer_mode='write',
                                            )
                response = outputs[0][2:].tolist()   #<s>: C
                #print(response)
                out_text = self.model.tokenizer.decode(response, add_special_tokens=True)
                print(out_text)

                try:
                    answer = out_text.lstrip()[0]
                    pre_img.append(images[len(pre_img) + ans2idx[answer]].cpu())
                except:
                    print('Select fail, use first image')
                    answer = 'A'
                    pre_img.append(images[len(pre_img) + ans2idx[answer]].cpu())
                selected[i] = ans2idx[answer]
        return selected

    def model_select_imagebase(self, output_text, locs, imagebase, progress):
        print('model_select_imagebase')
        pre_text = ''
        pre_img = []
        pre_text_list = []
        selected = []

        images = []
        for j in range(len(imagebase)):
            image = self.vis_processor(imagebase[j])
            images.append(image)
        images = torch.stack(images, dim=0).cuda()
        with torch.no_grad():
            with torch.cuda.amp.autocast():
                img_embeds = self.model.encode_img(images)

        for i, text in enumerate(output_text):
            pre_text += text + '\n'
            if i in locs:
                pre_text_list.append(pre_text)
                pre_text = ''
                print(img_embeds.shape)
                cand_embeds = torch.stack([item for j, item in enumerate(img_embeds) if j not in selected], dim=0)
                ans2idx = {}
                count = 0
                for j in range(len(img_embeds)):
                    if j not in selected:
                        ans2idx[chr(ord('A') + count)] = j
                        count += 1

                if cand_embeds.shape[0] > 1:
                    text = '根据给定上下文和候选图像，选择合适的配图：' + '<image>'.join(pre_text_list) + '候选图像包括: ' + '\n'.join([chr(ord('A') + j) + '.<image>' for j in range(len(cand_embeds))])
                    input_text = self.text2instruction(text) + '最合适的图是'
                    print(input_text)

                    all_img = cand_embeds if len(pre_img) == 0 else torch.cat(pre_img + [cand_embeds], dim=0)
                    input_embeds, im_mask, len_input_tokens = self.interleav_wrap(input_text, all_img)

                    with torch.no_grad():
                        outputs = self.model.generate(
                                                inputs_embeds=input_embeds,
                                                do_sample=True,
                                                temperature=1.,
                                                max_new_tokens=10,
                                                repetition_penalty=1.005,
                                                top_p=0.8,
                                                top_k=40,
                                                length_penalty=1.0,
                                                im_mask=im_mask,
                                                infer_mode='write',
                                                )
                    response = outputs[0][2:].tolist()   #<s>: C
                    #print(response)
                    out_text = self.model.tokenizer.decode(response, add_special_tokens=True)
                    print(out_text)

                    try:
                        answer = out_text.lstrip()[0]
                    except:
                        print('Select fail, use first image')
                        answer = 'A'
                else:
                    answer = 'A'

                pre_img.append(img_embeds[ans2idx[answer]].unsqueeze(0))
                selected.append(ans2idx[answer])
        selected = {loc: j for loc, j in zip(locs, selected)}
        print(selected)
        return selected

    def show_article(self, show_cap=False):
        md_shows = []
        imgs_show = []
        edit_bts = []
        for i in range(len(self.texts_imgs)):
            text, img = self.texts_imgs[i]
            md_shows.append(gr.Markdown(visible=True, value=text))
            edit_bts.append(gr.Button(visible=True, interactive=True, ))
            imgs_show.append(gr.Image(visible=False) if img is None else gr.Image(visible=True, value=img.paths[img.pts]))

        print(f'show {len(md_shows)} text sections')
        for _ in range(max_section - len(self.texts_imgs)):
            md_shows.append(gr.Markdown(visible=False, value=''))
            edit_bts.append(gr.Button(visible=False))
            imgs_show.append(gr.Image(visible=False))

        return md_shows + edit_bts + imgs_show

    def generate_article(self, instruction, upimages, beam, repetition, max_length, random, seed):
        self.reset()

        set_random_seed(int(seed))
        self.hash_folder = hashlib.sha256(instruction.encode()).hexdigest()
        self.instruction = instruction
        if upimages is None:
            upimages = []
        else:
            upimages = [t.image.path for t in upimages.root]
        img_instruction = '<image> ' * len(upimages)
        instruction = img_instruction.strip() + instruction
        text = self.text2instruction(instruction)
        print('random generate:{}'.format(random))
        if article_stream_output:
            if len(upimages) == 0:
                input_ids = self.model.tokenizer(text, return_tensors="pt")['input_ids']
                input_embeds = self.model.model.tok_embeddings(input_ids.cuda())
                im_mask = None
            else:
                images = []
                for j in range(len(upimages)):
                    image = self.vis_processor(upimages[j])
                    images.append(image)
                images = torch.stack(images, dim=0)
                with torch.no_grad():
                    with torch.cuda.amp.autocast():
                        img_embeds = self.model.encode_img(images)

                text = self.text2instruction(instruction)

                input_embeds, im_mask, len_input_tokens = self.interleav_wrap(text, img_embeds)

            print(text)
            generate_params = dict(
                inputs_embeds=input_embeds,
                do_sample=random,
                stopping_criteria=self.stopping_criteria,
                repetition_penalty=float(repetition),
                max_new_tokens=max_length,
                top_p=0.8,
                top_k=40,
                length_penalty=1.0,
                im_mask=im_mask,
                infer_mode='write',
            )
            output_text = "▌"
            with self.generate_with_streaming(**generate_params) as generator:
                for output in generator:
                    decoded_output = self.model.tokenizer.decode(output[1:])
                    if output[-1] in [self.model.tokenizer.eos_token_id, 92542]:
                        break
                    output_text = decoded_output.replace('\n', '\n\n') + "▌"
                    yield (output_text,) + (gr.Markdown(visible=False),) * (max_section - 1) + (
                            gr.Button(visible=False),) * max_section + (gr.Image(visible=False),) * max_section
                    time.sleep(0.01)
            output_text = output_text[:-1]
            yield (output_text,) + (gr.Markdown(visible=False),) * (max_section - 1) + (
                            gr.Button(visible=False),) * max_section + (gr.Image(visible=False),) * max_section
        else:
            output_text = self.generate(text, random, beam, max_length, repetition)

        output_text = re.sub(r'(\n\s*)+', '\n', output_text.strip())
        print(output_text)

        output_text = output_text.split('\n')[:max_section]

        self.texts_imgs = [[t, None] for t in output_text]
        self.database.addtitle(text, self.hash_folder, params={'beam':beam, 'repetition':repetition, 'max_length':max_length, 'random':random, 'seed':seed})

        if article_stream_output:
            yield self.show_article()
        else:
            return self.show_article()

    def insert_images(self, upimages, llmO, img_num, seed, progress=gr.Progress()):
        set_random_seed(int(seed))
        if not llmO:
            output_text = [t[0] for t in self.texts_imgs]
            idx_text_sections = [f'<Seg{i}>' + ' ' + it + '\n' for i, it in enumerate(output_text)]

            if img_num == 'Automatic (自动)':
                img_num = ''

            if upimages is None:
                upimages = []
            else:
                upimages = [t.image.path for t in upimages.root]

            inject_text, locs = self.generate_loc(idx_text_sections, upimages, img_num)
            if len(upimages) == 0:
                caps = self.generate_cap(idx_text_sections, locs, progress)

                self.ex_idxs = []
                images_paths = {}
                for loc, cap in progress.tqdm(caps.items(), desc="download image"):
                    idxs = self.get_images_xlab(cap, self.img_pt, self.ex_idxs)
                    paths = [os.path.join('articles', self.hash_folder, f'temp_{self.img_pt}_{i}.png') for i in range(4)]
                    images_paths[loc] = [it for it in paths if os.path.exists(it)]
                    if len(images_paths[loc]) == 0:
                        gr.Warning('Image download fail !!!')
                        del images_paths[loc]
                    self.img_pt += 1
                    self.ex_idxs.extend(idxs)

                locs = [k for k in caps.keys() if k in images_paths]

                if True:
                    selected = self.model_select_image(output_text, locs, images_paths, progress)
                else:
                    selected = {k: 0 for k in locs}

                self.texts_imgs = [
                    [t, ImageGroup(caps[i], images_paths[i], selected[i])] if i in selected else [t, None]
                    for i, t in enumerate(output_text)]
            else:
                selected = self.model_select_imagebase(output_text, locs, upimages, progress)
                self.texts_imgs = [[t, ImageGroup('', [upimages[selected[i]]])] if i in selected else [t, None] for i, t in enumerate(output_text)]

        self.database.addarticle(self.texts_imgs)
        return self.show_article()

    def show_edit(self, text, pt):
        if self.open_edit and pt != self.pt:
            gr.Warning('Please close the editing panel before open another editing panel !!!')
            return gr.Accordion(visible=False), text, ''
        else:
            self.pt = pt
            self.open_edit = True
            return gr.Accordion(visible=True), text, ''

    def show_gallery(self, img_pt):
        if self.open_edit and img_pt != self.pt:
            gr.Warning('Please close the editing panel before open another editing panel !!!')
            return gr.Accordion(visible=False), '', gr.Gallery()
        elif len(self.texts_imgs[img_pt][1].paths) == 1:
            gr.Warning('This imag can not be edited !!!')
            return gr.Accordion(visible=False), '', gr.Gallery()
        else:
            self.pt = img_pt
            self.open_edit = True
            gallery = gr.Gallery(value=self.texts_imgs[img_pt][1].paths)
            return gr.Accordion(visible=True), self.texts_imgs[img_pt][1].cap, gallery

    def hide_edit(self, flag=False):
        self.open_edit = flag
        return gr.Accordion(visible=False), None, gr.Textbox(value='', interactive=False), ''

    def hide_gallery(self):
        self.open_edit = False
        self.database.addedit('changeimage', '', self.texts_imgs)
        return gr.Accordion(visible=False), '', gr.Gallery(value=None)

    def delete_gallery(self, pt):
        self.texts_imgs[pt][1] = None
        return [gr.Image(visible=False, value=None)] + list(self.hide_gallery())

    def edit_types_change(self, edit_type):
        if edit_type in ['缩写', 'abbreviate']:
            return gr.Textbox(interactive=False)
        elif edit_type in ['扩写', '改写', '前插入一段', '后插入一段', 'expand', 'rewrite', 'insert a paragraph before', 'insert a paragraph after']:
            return gr.Textbox(interactive=True)

    def insert_image(self):
        return list(self.hide_edit(flag=True)) + [gr.Accordion(visible=True), '', gr.Gallery(visible=True, value=None)]

    def done_edit(self, edit_type, inst_edit, new_text):
        if new_text == '':
            self.texts_imgs = self.texts_imgs[:self.pt] + self.texts_imgs[self.pt+1:]
        else:
            sub_text = re.sub(r'\n+', ' ', new_text)
            if edit_type in ['扩写', '缩写', '改写', 'expand', 'rewrite', 'abbreviate']:
                self.texts_imgs[self.pt][0] = sub_text
            elif edit_type in ['前插入一段', 'insert a paragraph before']:
                self.texts_imgs = self.texts_imgs[:self.pt] + [[sub_text, None]] + self.texts_imgs[self.pt:]
            elif edit_type in ['后插入一段', 'insert a paragraph after']:
                self.texts_imgs = self.texts_imgs[:self.pt+1] + [[sub_text, None]] + self.texts_imgs[self.pt+1:]
            else:
                print(new_text)
                assert 0 == 1

        self.database.addedit(edit_type, inst_edit, self.texts_imgs)
        return list(self.hide_edit()) + list(self.show_article())

    def paragraph_edit(self, edit_type, text, instruction, pts):
        if edit_type in ['扩写', 'expand']:
            inst_text = f'扩写以下段落：{text}\n基于以下素材：{instruction}'
        elif edit_type in ['改写', 'rewrite']:
            inst_text = f'改写以下段落：{text}\n基于以下素材：{instruction}'
        elif edit_type in ['缩写', 'abbreviate']:
            inst_text = '缩写以下段落：' + text
        elif edit_type in ['前插入一段', 'insert a paragraph before']:
            pre_text = '' if pts == 0 else self.texts_imgs[pts-1][0]
            inst_text = f'在以下两段中插入一段。\n第一段：{pre_text}\n第二段：{text}\n插入段的大纲：{instruction}'
        elif edit_type in ['后插入一段', 'insert a paragraph after']:
            post_text = '' if pts + 1 >= len(self.texts_imgs) else self.texts_imgs[pts + 1][0]
            inst_text = f'在以下两段中插入一段。\n第一段：{text}\n第二段：{post_text}\n插入段的大纲：{instruction}'
        elif edit_type is None:
            if article_stream_output:
                yield text, gr.Button(interactive=True), gr.Button(interactive=True)
            else:
                return text, gr.Button(interactive=True), gr.Button(interactive=True)

        if instruction == '' and edit_type in ['前插入一段', '后插入一段', 'insert a paragraph before', 'insert a paragraph after']:
            gr.Warning('Please input the instruction !!!')
            if article_stream_output:
                yield '', gr.Button(interactive=True), gr.Button(interactive=True)
            else:
                return '', gr.Button(interactive=True), gr.Button(interactive=True)
        else:
            print(inst_text)
            instruction = self.text2instruction(inst_text)
            if article_stream_output:
                input_ids = self.model.tokenizer(instruction, return_tensors="pt")['input_ids']
                len_input_tokens = len(input_ids[0])
                input_embeds = self.model.model.tok_embeddings(input_ids.cuda())
                generate_params = dict(
                    inputs_embeds=input_embeds,
                    do_sample=True,
                    stopping_criteria=self.stopping_criteria,
                    repetition_penalty=1.005,
                    max_length=500 - len_input_tokens,
                    top_p=0.8,
                    top_k=40,
                    length_penalty=1.0
                )
                output_text = "▌"
                with self.generate_with_streaming(**generate_params) as generator:
                    for output in generator:
                        decoded_output = self.model.tokenizer.decode(output[1:])
                        if output[-1] in [self.model.tokenizer.eos_token_id, 92542]:
                            break
                        output_text = decoded_output.replace('\n', '\n\n') + "▌"
                        yield output_text, gr.Button(interactive=False), gr.Button(interactive=False)
                        time.sleep(0.1)
                output_text = output_text[:-1]
                print(output_text)
                yield output_text, gr.Button(interactive=True), gr.Button(interactive=True)
            else:
                output_text = self.generate(text, True, 1, 500, 1.005)
                return output_text, gr.Button(interactive=True), gr.Button(interactive=True)

    def search_image(self, text, pt):
        if text == '':
            return gr.Gallery()

        idxs = self.get_images_xlab(text, self.img_pt, self.ex_idxs)
        images_paths = [os.path.join('articles', self.hash_folder, f'temp_{self.img_pt}_{i}.png') for i in
                             range(4)]
        self.img_pt += 1
        self.ex_idxs.extend(idxs)

        self.texts_imgs[pt][1] = ImageGroup(text, images_paths)

        ga_show = gr.Gallery(visible=True, value=images_paths)
        return ga_show, gr.Image(visible=True, value=images_paths[0])

    def replace_image(self, pt, evt: gr.SelectData):
        self.texts_imgs[pt][1].pts = evt.index
        img = self.texts_imgs[pt][1]
        return gr.Image(visible=True, value=img.paths[img.pts])

    def save(self, beam, repetition, text_num, random, seed):
        folder = 'save_articles/' + self.hash_folder
        if os.path.exists(folder):
            for item in os.listdir(folder):
                os.remove(os.path.join(folder, item))
        os.makedirs(folder, exist_ok=True)

        save_text = '\n'.join([self.instruction, str(beam), str(repetition), str(text_num), str(random), str(seed)]) + '\n\n'
        if len(self.texts_imgs) > 0:
            for txt, img in self.texts_imgs:
                save_text += txt + '\n'
                if img is not None:
                    save_text += f'<div align="center"> <img src={os.path.basename(img.paths[img.pts])} width = 500/> </div>'
                    path = os.path.join('articles', self.hash_folder, os.path.basename(img.paths[img.pts]))
                    if os.path.exists(path):
                        shutil.copy(path, folder)
                    else:
                        shutil.copy(img.paths[img.pts], folder)

        with open(os.path.join(folder, 'io.MD'), 'w') as f:
            f.writelines(save_text)

        archived = shutil.make_archive(folder, 'zip', folder)
        return archived

    def generate_with_callback(self, callback=None, **kwargs):
        kwargs.setdefault("stopping_criteria",
                          transformers.StoppingCriteriaList())
        kwargs["stopping_criteria"].append(Stream(callback_func=callback))
        with torch.no_grad():
            self.model.generate(**kwargs)

    def generate_with_streaming(self, **kwargs):
        return Iteratorize(self.generate_with_callback, kwargs, callback=None)

    def change_meta(self, withmeta):
        self.withmeta = withmeta

    def upload_images(self, files):
        if len(files) > 10:
            gr.Warning('No more than 10 images !!!')
            files = files[:10]

        return gr.Gallery(value=files), gr.Dropdown(value=str(len(files)))

    def clear_images(self):
        return gr.Gallery(value=None)

    def limit_imagenum(self, img_num, upshows):
        if upshows is None:
            return gr.Dropdown()
        maxnum = len(upshows.root)
        if img_num == 'Automatic (自动)' or int(img_num) > maxnum:
            img_num = str(maxnum)
        return gr.Dropdown(value=img_num)

    def enable_like(self):
        return [gr.Button(visible=True)] * 2

    def like(self):
        with open(os.path.join(self.database.folder, 'like.txt'), 'w') as fd:
            fd.write('like')
        return [gr.Button(visible=False)] * 2

    def dislike(self):
        with open(os.path.join(self.database.folder, 'like.txt'), 'w') as fd:
            fd.write('dislike')
        return [gr.Button(visible=False)] * 2


def change_language(lang):
    edit_types, inst_edits, insertIMGs, edit_dones, edit_cancels = [], [], [], [], []
    cap_searchs, gallery_dels, gallery_dones = [], [], []
    if lang == '中文':
        lang_btn = gr.Button(value='English')
        for _ in range(max_section):
            edit_types.append(gr.Radio(["改写", "扩写", "缩写", "前插入一段", "后插入一段"]))
            inst_edits.append(gr.Textbox(label='插入段落时，请输入插入段的大纲：'))
            insertIMGs.append(gr.Button(value='在下方插入图片'))
            edit_dones.append(gr.Button(value='确定'))
            edit_cancels.append(gr.Button(value='取消'))
            cap_searchs.append(gr.Button(value='搜图'))
            gallery_dels.append(gr.Button(value='删除'))
            gallery_dones.append(gr.Button(value='确定'))
    elif lang == 'English':
        lang_btn = gr.Button(value='中文')
        for _ in range(max_section):
            edit_types.append(gr.Radio(["rewrite", "expand", "abbreviate", "insert a paragraph before", "insert a paragraph after"]))
            inst_edits.append(gr.Textbox(label='Instrcution for editing:'))
            insertIMGs.append(gr.Button(value='Insert image below'))
            edit_dones.append(gr.Button(value='Done'))
            edit_cancels.append(gr.Button(value='Cancel'))
            cap_searchs.append(gr.Button(value='Search'))
            gallery_dels.append(gr.Button(value='Delete'))
            gallery_dones.append(gr.Button(value='Done'))

    return [lang_btn] + edit_types + inst_edits + insertIMGs + edit_dones + edit_cancels + cap_searchs + gallery_dels + gallery_dones


parser = argparse.ArgumentParser()
parser.add_argument("--code_path", default='internlm/internlm-xcomposer2d5-7b')
parser.add_argument("--private", default=False, action='store_true')
parser.add_argument("--num_gpus", default=1, type=int)
parser.add_argument("--port", default=7861, type=int)
args = parser.parse_args()
demo_ui = Demo_UI(args.code_path, args.num_gpus)


with gr.Blocks(css=custom_css, title='浦语·灵笔 (InternLM-XComposer)') as demo:
    with gr.Row():
        with gr.Column(scale=20):
            # gr.HTML("""<h1 align="center" id="space-title" style="font-size:35px;">🤗 浦语·灵笔 (InternLM-XComposer)</h1>""")
            gr.HTML(
                """<h1 align="center">InternLM-XComposer</h1>"""
            )
        with gr.Column(scale=1, min_width=100):
            lang_btn = gr.Button("中文")

    with gr.Tabs(elem_classes="tab-buttons") as tabs:
        with gr.TabItem("📝 Write Interleaved-text-image Article (创作图文并茂文章)"):
            with gr.Row():
                with gr.Column(scale=2):
                    instruction = gr.Textbox(label='Write an illustrated article based on the given instruction: (根据素材或指令创作图文并茂的文章)',
                                             lines=5,
                                             value='''阅读下面的材料，根据要求写作。\n电影《长安三万里》的出现让人感慨，影片并未将重点全落在大唐风华上，也展现了恢弘气象的阴暗面，即旧门阀的资源垄断、朝政的日益衰败与青年才俊的壮志难酬。高适仕进无门，只能回乡沉潜修行。李白虽得玉真公主举荐，擢入翰林，但他只是成为唐玄宗的御用文人，不能真正实现有益于朝政的志意。然而，片中高潮部分《将进酒》一节，人至中年、挂着肚腩的李白引众人乘仙鹤上天，一路从水面、瀑布飞升至银河进入仙宫，李白狂奔着与仙人们碰杯，最后大家纵身飞向漩涡般的九重天。肉身的微贱、世路的“天生我材必有用，坎坷，拘不住精神的高蹈。“天生我材必有用，千金散尽还复来。”\n古往今来，身处闲顿、遭受挫折、被病痛折磨，很多人都曾经历了人生的“失意”，却反而成就了他们“诗意”的人生。对正在追求人生价值的当代青年来说，如何对待人生中的缺憾和困顿?诗意人生中又有怎样的自我坚守和自我认同?请结合“失意”与“诗意”这两个关键词写一篇文章。\n要求:选准角度，确定立意，明确文体，自拟标题;不要套作，不得抄袭;不得泄露个人信息;不少于 800 字。''')
                with gr.Column(scale=1):
                    img_num = gr.Dropdown(
                        ["Automatic (自动)", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                        value='1', label="Image Number (插图数量)", info="Select the number of the inserted images",
                        interactive=True)
                    seed = gr.Slider(minimum=1.0, maximum=20000.0, value=1234.0, step=1.0, label='Random Seed (随机种子)')
                    btn = gr.Button("Submit (提交)", scale=1)

            with gr.Accordion("Click to add image material (点击添加图片素材）, optional（可选）", open=False, visible=True):
                with gr.Row():
                    uploads = gr.File(file_count='multiple', scale=1)
                    upshows = gr.Gallery(columns=4, scale=2)

            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Accordion("Advanced Settings (高级设置)", open=False, visible=True) as parameter_article:
                        beam = gr.Slider(minimum=1.0, maximum=6.0, value=1.0, step=1.0, label='Beam Size (集束大小)')
                        repetition = gr.Slider(minimum=1.0, maximum=2.0, value=1.005, step=0.001, label='Repetition_penalty (重复惩罚)')
                        text_num = gr.Slider(minimum=100.0, maximum=8192.0, value=8192.0, step=1.0, label='Max output tokens (最多输出字数)')
                        llmO = gr.Checkbox(value=True, label='LLM Only (纯文本写作)')
                        random = gr.Checkbox(value=True, label='Sampling (随机采样)')
                        withmeta = gr.Checkbox(value=False, label='With Meta (使用meta指令)')

            with gr.Row():
                btn_like = gr.Button(interactive=True, visible=False, value='👍  Like This Article (点赞这篇文章)')
                btn_dislike = gr.Button(interactive=True, visible=False, value='👎  Dislike This Article (点踩这篇文章)')

            articles, edit_bts = [], []
            text_editers, edit_types, edit_subs, insertIMGs, edit_dones, edit_cancels = [], [], [], [], [], []
            before_edits, inst_edits, after_edits = [], [], []
            img_editers, cap_boxs, cap_searchs, gallerys, gallery_dels, gallery_dones = [], [], [], [], [], []
            image_shows = []
            with gr.Column():
                for i in range(max_section):
                    visible = True if i == 0 else False
                    with gr.Row():
                        with gr.Column(scale=3):
                            articles.append(gr.Markdown(visible=visible, elem_classes='feedback'))

                        edit_bts.append(gr.Button(interactive=True, visible=False, value='\U0001F58C', elem_classes='sm_btn'))
                        with gr.Column(scale=2):
                            with gr.Accordion('Text Editing (文本编辑)', open=True, visible=False) as text_editer:
                                gr.HTML('<p style="color:gray;">Befor Editing (编辑前):</p>', elem_classes='edit')
                                gr.HTML('<p style="color:gray;">===========</p>', elem_classes='edit')
                                before_edits.append(gr.HTML('', elem_classes='edit'))
                                gr.HTML('<p style="color:gray;">===========</p>', elem_classes='edit')

                                edit_types.append(gr.Radio(["rewrite", "expand", "abbreviate", "insert a paragraph before", "insert a paragraph after"], label="Paragraph modification (段落修改)",
                                                     info="选择后点击右侧按钮，模型自动修改", elem_classes='editsmall'))
                                with gr.Row():
                                    inst_edits.append(gr.Textbox(label='Instrcution for editing:', interactive=False, elem_classes='editsmall'))
                                    edit_subs.append(gr.Button(elem_classes='smax_btn'))

                                gr.HTML('<p style="color:gray;">After Editing (编辑后):</p>', elem_classes='edit')
                                after_edits.append(gr.Textbox(show_label=False, elem_classes='edit'))

                                with gr.Row():
                                    insertIMGs.append(gr.Button(value='Insert image below'))
                                    edit_dones.append(gr.Button(value='Done'))
                                    edit_cancels.append(gr.Button(value='Cancel'))

                    with gr.Row():
                        with gr.Column(scale=3):
                            image_shows.append(gr.Image(visible=False, width=600, elem_classes='feedback'))

                        with gr.Column(scale=2):
                            with gr.Accordion('Images Editing (图片编辑)', open=True, visible=False) as img_editer:
                                with gr.Row():
                                    cap_boxs.append(gr.Textbox(label='image caption (图片标题)', interactive=True, scale=6))
                                    cap_searchs.append(gr.Button(value="Search", scale=1))
                                with gr.Row():
                                    gallerys.append(gr.Gallery(columns=2, height='auto'))

                                with gr.Row():
                                    gallery_dels.append(gr.Button(value="Delete"))
                                    gallery_dones.append(gr.Button(value="Done"))

                    text_editers.append(text_editer)
                    img_editers.append(img_editer)

            save_btn = gr.Button("Save article (保存文章)")
            save_file = gr.File(label="Save article (保存文章)")
            save_btn.click(demo_ui.save, inputs=[beam, repetition, text_num, random, seed], outputs=save_file)

            uploads.upload(demo_ui.upload_images, inputs=uploads, outputs=[upshows, img_num])
            uploads.clear(demo_ui.clear_images, inputs=[], outputs=upshows)
            img_num.select(demo_ui.limit_imagenum, inputs=[img_num, upshows], outputs=img_num)

            withmeta.change(demo_ui.change_meta, inputs=withmeta, outputs=[])

            for i in range(max_section):
                edit_bts[i].click(demo_ui.show_edit, inputs=[articles[i], gr.Number(value=i, visible=False)], outputs=[text_editers[i], before_edits[i], after_edits[i]])
                edit_types[i].select(demo_ui.edit_types_change, inputs=[edit_types[i]], outputs=[inst_edits[i]])
                edit_subs[i].click(demo_ui.paragraph_edit, inputs=[edit_types[i], before_edits[i], inst_edits[i], gr.Number(value=i, visible=False)], outputs=[after_edits[i], insertIMGs[i], edit_dones[i]])
                insertIMGs[i].click(demo_ui.insert_image, inputs=[], outputs=[text_editers[i], edit_types[i], inst_edits[i], after_edits[i], img_editers[i], cap_boxs[i], gallerys[i]])
                edit_dones[i].click(demo_ui.done_edit, inputs=[edit_types[i], inst_edits[i], after_edits[i]], outputs=[text_editers[i], edit_types[i], inst_edits[i], after_edits[i]] + articles + edit_bts + image_shows)
                edit_cancels[i].click(demo_ui.hide_edit, inputs=[], outputs=[text_editers[i], edit_types[i], inst_edits[i], after_edits[i]])

                image_shows[i].select(demo_ui.show_gallery, inputs=[gr.Number(value=i, visible=False)], outputs=[img_editers[i], cap_boxs[i], gallerys[i]])
                cap_searchs[i].click(demo_ui.search_image, inputs=[cap_boxs[i], gr.Number(value=i, visible=False)], outputs=[gallerys[i], image_shows[i]])
                gallerys[i].select(demo_ui.replace_image, inputs=[gr.Number(value=i, visible=False)], outputs=[image_shows[i]])
                gallery_dels[i].click(demo_ui.delete_gallery, inputs=[gr.Number(value=i, visible=False)], outputs=[image_shows[i], img_editers[i], cap_boxs[i], gallerys[i]])
                gallery_dones[i].click(demo_ui.hide_gallery, inputs=[], outputs=[img_editers[i], cap_boxs[i], gallerys[i]])

            btn_like.click(demo_ui.like, inputs=[], outputs=[btn_like, btn_dislike])
            btn_dislike.click(demo_ui.dislike, inputs=[], outputs=[btn_like, btn_dislike])

            btn.click(demo_ui.reset_components, inputs=[],
                      outputs=articles + edit_bts + image_shows + text_editers + img_editers).then(
                    demo_ui.generate_article,
                    inputs=[instruction, upshows, beam, repetition, text_num, random, seed],
                    outputs=articles + edit_bts + image_shows).then(
                    demo_ui.insert_images, inputs=[upshows, llmO, img_num, seed], outputs=articles + edit_bts + image_shows).then(
                    demo_ui.enable_like, inputs=[], outputs=[btn_like, btn_dislike])


    lang_btn.click(change_language, inputs=lang_btn, outputs=[lang_btn] + edit_types + inst_edits + insertIMGs + edit_dones + edit_cancels + cap_searchs + gallery_dels + gallery_dones)

if __name__ == "__main__":
    if args.private:
        demo.queue().launch(share=False, server_name="127.0.0.1", server_port=args.port, max_threads=1)
    else:
        demo.queue().launch(share=True, server_name="0.0.0.0", server_port=args.port, max_threads=1)

