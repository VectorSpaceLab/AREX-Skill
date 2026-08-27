# SimpleCV API Reference

## When to read this

Read this when a task needs a verified class constructor, common method signature, or public API boundary before using a workflow sub-skill. Signatures were confirmed from an installed SimpleCV 1.3.0 package in a Python 2.7/OpenCV 2.4-compatible environment.

## Core constructors

| API | Verified signature | Notes |
|---|---|---|
| `Image` | `Image(source=None, camera=None, colorSpace=ColorSpace.UNKNOWN, verbose=True, sample=False, cv2image=False, webp=False)` | Accepts filenames, sample names, numpy arrays, PIL/cv objects, URLs, and camera sources depending on dependencies. |
| `ImageSet` | `ImageSet(directory=None)` | Loads from directories, lists, or `samples`/`sample`; inherits from `list`. |
| `ColorModel` | `ColorModel(data=None, isBackground=True)` | Builds foreground/background color models used by thresholding and color segmentation. |
| `Display` | `Display(resolution=(640, 480), flags=0, title='SimpleCV', displaytype='standard', headless=False)` | Pygame-backed display; use headless/dummy SDL in non-interactive sessions. |
| `Camera` | `Camera(camera_index=-1, prop_set={}, threaded=True, calibrationfile='')` | Physical camera wrapper; hardware-dependent. |
| `VirtualCamera` | `VirtualCamera(s, st, start=1)` | Uses image or video sources as frame sources; useful for safe checks. |
| `JpegStreamCamera` | `JpegStreamCamera(url)` | Reads JPEG stream URLs; network/service-dependent. |
| `Kinect` | `Kinect(device_number=0)` | Optional `freenect` hardware integration. |
| `StereoImage` | `StereoImage(imgLeft, imgRight)` | Pair of images for stereo routines. |
| `StereoCamera` | `StereoCamera()` | Physical stereo camera workflow; hardware-dependent. |
| `HaarCascade` | `HaarCascade(fname=None, name=None)` | Loads built-in or file-backed Haar cascades. |
| `DFT` | `DFT(**kwargs)` | Frequency-domain filter helper; see image-processing sub-skill. |
| `LineScan` | `LineScan(args, **kwargs)` | List-like intensity profile helper. |

## Important `Image` methods

| Method | Verified signature | Typical owner |
|---|---|---|
| `findBlobs` | `findBlobs(threshval=-1, minsize=10, maxsize=0, threshblocksize=0, threshconstant=5, appx_level=3)` | `feature-detection` |
| `findLines` | `findLines(threshold=80, minlinelength=30, maxlinegap=10, cannyth1=50, cannyth2=100, useStandard=False, nLines=-1, maxpixelgap=1)` | `feature-detection` |
| `findTemplate` | `findTemplate(template_image=None, threshold=5, method='SQR_DIFF_NORM', grayscale=True, rawmatches=False)` | `feature-detection` |
| `findTemplateOnce` | `findTemplateOnce(template_image=None, threshold=0.2, method='SQR_DIFF_NORM', grayscale=True)` | `feature-detection` |
| `findCircle` | `findCircle(canny=100, thresh=350, distance=-1)` | `feature-detection` |
| `findKeypoints` | `findKeypoints(min_quality=300.0, flavor='SURF', highQuality=False)` | `feature-detection` |
| `findKeypointMatch` | `findKeypointMatch(template, quality=500.0, minDist=0.2, minMatch=0.4)` | `feature-detection` |
| `track` | `track(method='CAMShift', ts=None, img=None, bb=None, **kwargs)` | `segmentation-tracking` |
| `findMotion` | `findMotion(previous_frame, window=11, method='BM', aggregate=True)` | `segmentation-tracking` |
| `binarize` | `binarize(thresh=-1, maxv=255, blocksize=0, p=5)` | `image-processing-basics` |
| `crop` | `crop(x, y=None, w=None, h=None, centered=False, smart=False)` | `image-processing-basics` |
| `scale` | `scale(width, height=-1, interpolation=cv2.INTER_LINEAR)` | `image-processing-basics` |
| `resize` | `resize(w=None, h=None)` | `image-processing-basics` |
| `save` | `save(filehandle_or_filename='', mode='', verbose=False, temp=False, path=None, filename=None, cleanTemp=False, **params)` | `image-processing-basics` |
| `show` | `show(type='window')` | `acquisition-display-shell` |
| `edges` | `edges(t1=50, t2=100)` | `image-processing-basics` / `feature-detection` |
| `rotate` | `rotate(angle, fixed=True, point=[-1, -1], scale=1.0)` | `image-processing-basics` |
| `warp` | `warp(cornerpoints)` | `image-processing-basics` |
| `shear` | `shear(cornerpoints)` | `image-processing-basics` |
| `findHaarFeatures` | `findHaarFeatures(cascade, scale_factor=1.2, min_neighbors=2, use_canny=1, min_size=(20, 20), max_size=(1000, 1000))` | `feature-detection` |
| `findBarcode` | `findBarcode(doZLib=True, zxing_path='')` | `feature-detection` with optional ZXing |
| `readText` | `readText()` | `feature-detection` with optional tesseract |

## Feature and segmentation APIs

| API | Role |
|---|---|
| `FeatureSet` | List-like collection with sorting/filtering/drawing helpers and coordinate arrays. |
| `Feature` | Base object for points, lines, blobs, templates, and other detections. |
| `Blob` | Rich geometry object with area, radius, contour, hull, masks, and shape-context helpers. |
| `ColorSegmentation` | Maintains a color model and produces segmented images/blobs. |
| `DiffSegmentation(grayOnly=False, threshold=(10,10,10))` | Frame differencing segmentation model. |
| `RunningSegmentation(alpha=0.7, thresh=(20,20,20))` | Running-average background segmentation model. |
| `MOGSegmentation(history=200, nMixtures=5, backgroundRatio=0.7, noiseSigma=15, learningRate=0.7)` | Mixture-of-Gaussians background segmentation wrapper. |

## Legacy classifier APIs

| API | Verified signature | Notes |
|---|---|---|
| `KNNClassifier` | `KNNClassifier(featureExtractors, k=1, dist=None)` | Uses feature extractors and raw image data. |
| `NaiveBayesClassifier` | `NaiveBayesClassifier(featureExtractors)` | Similar train/test/save/load pattern to KNN. |
| `TreeClassifier` | `TreeClassifier(featureExtractors=[], flavor='Tree', flavorDict=None)` | Tree/forest/flavor options are legacy. |
| `SVMClassifier` | `SVMClassifier(featureExtractors, properties=None)` | Requires the optional Orange stack; treat as optional unless provisioned. |

## API usage rules

- Prefer static `Image` workflows and package sample names for automated checks.
- Treat `Camera`, `Display`, and `show()` calls as interactive/hardware-sensitive.
- For feature and segmentation methods, always validate `None` or empty `FeatureSet` results before drawing or indexing.
- For classifier wrappers, keep feature extractors identical between training and classification.
- Optional integrations should be tested separately before the main workflow claims they are available.
