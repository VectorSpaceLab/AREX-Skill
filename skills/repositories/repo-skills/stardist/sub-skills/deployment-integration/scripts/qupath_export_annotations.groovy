/*
 * Bundled StarDist/QuPath handoff: export project annotations as image and
 * integer-label TIFFs under <project>/ground_truth/{images,masks}.
 *
 * Prerequisites: QuPath with its ImageJ extension, an open project image, and
 * permission to write beneath the project directory. Review channel_of_interest
 * and downsample for the target image before running "Run for project".
 */
def channel_of_interest = 1 // null exports all channels
def downsample = 1
def image_name = getProjectEntry().getImageName()
def rm = RoiManager.getRoiManager() ?: new RoiManager()
createSelectAllObject(true)
def fullimage_annotation = getSelectedObject()
def imageData = getCurrentImageData()
def server = imageData.getServer()
def viewer = getCurrentViewer()
def hierarchy = getCurrentHierarchy()
def request = RegionRequest.createInstance(server.getServerPath(), downsample, fullimage_annotation.getROI())
def pathImage = IJExtension.extractROIWithOverlay(server, fullimage_annotation, hierarchy, request, false, viewer.getOverlayOptions())
def image = pathImage.getImage()
def labels = IJ.createImage("Labels", "16-bit black", image.getWidth(), image.getHeight(), 1)
IJ.run(image, "To ROI Manager", "")
def label_ip = labels.getProcessor()
def idx = 0
rm.getRoisAsArray().each { roi ->
    if (roi.getType() != Roi.RECTANGLE) {
        label_ip.setColor(++idx)
        label_ip.setRoi(roi)
        label_ip.fill(roi)
    }
}
labels.setProcessor(label_ip)
def output = image
if (channel_of_interest != null) output = ChannelSplitter.split(image)[channel_of_interest - 1]
saveImages(output, labels, image_name)
output.close(); labels.close(); image.close()
removeObject(fullimage_annotation, true)

void saveImages(def images, def labels, def name) {
    def source_folder = new File(buildFilePath(PROJECT_BASE_DIR, 'ground_truth', 'images'))
    def target_folder = new File(buildFilePath(PROJECT_BASE_DIR, 'ground_truth', 'masks'))
    mkdirs(source_folder.getAbsolutePath()); mkdirs(target_folder.getAbsolutePath())
    IJ.save(images, new File(source_folder, name).getAbsolutePath() + '.tif')
    IJ.save(labels, new File(target_folder, name).getAbsolutePath() + '.tif')
}

import qupath.lib.roi.RectangleROI
import qupath.imagej.gui.IJExtension
import qupath.lib.regions.RegionRequest
import ij.IJ
import ij.gui.Roi
import ij.plugin.ChannelSplitter
import ij.plugin.frame.RoiManager
