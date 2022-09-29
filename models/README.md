# ONNX models
## Obtaining the models <a id="obtain-models"></a>
The ONNX models for the examples can be found at [ONNX Model Zoo](https://github.com/onnx/models). A `git clone`
of the repository is not required. Instead, follow the [git-lfs instructions](https://github.com/onnx/models#usage---git-lfs-) in the
[ONNX Model Zoo README.md](https://github.com/onnx/models#onnx-model-zoo) to download a single model.

## Example models
The following models are used in the examples:
1. [mnist-8](https://github.com/onnx/models/tree/main/vision/classification/mnist)
1. [resnet50-caffe2-v1-8](https://github.com/onnx/models/tree/main/vision/classification/resnet)
1. [mobilenetv2-7.onnx](https://github.com/onnx/models/tree/main/vision/classification/mobilenet/model)

## Verified ONNX Model Zoo models <a id="verified-models"></a>
The following list of ONNX models from the [ONNX Model Zoo](https://github.com/onnx/models) have been built and verified with the IBM Z Deep Learning Compiler:

| Model Group | Model |
| ------------------ | --------------- |
| Alexnet | [bvlcalexnet-6](https://github.com/onnx/models/tree/main/vision/classification/alexnet) |
|  | [bvlcalexnet-7](https://github.com/onnx/models/tree/main/vision/classification/alexnet) |
|  | [bvlcalexnet-8](https://github.com/onnx/models/tree/main/vision/classification/alexnet) |
|  | [bvlcalexnet-9](https://github.com/onnx/models/tree/main/vision/classification/alexnet) |
|  | [bvlcalexnet-12](https://github.com/onnx/models/tree/main/vision/classification/alexnet) |
| Bert-squad | [bertsquad-10](https://github.com/onnx/models/tree/main/text/machine_comprehension/bert-squad) |
|  | [bertsquad-12](https://github.com/onnx/models/tree/main/text/machine_comprehension/bert-squad) |
| Caffenet | [caffenet-6](https://github.com/onnx/models/tree/main/vision/classification/caffenet) |
|  | [caffenet-7](https://github.com/onnx/models/tree/main/vision/classification/caffenet) |
|  | [caffenet-8](https://github.com/onnx/models/tree/main/vision/classification/caffenet) |
|  | [caffenet-9](https://github.com/onnx/models/tree/main/vision/classification/caffenet) |
|  | [caffenet-12](https://github.com/onnx/models/tree/main/vision/classification/caffenet) |
| Densenet-121 | [densenet-6](https://github.com/onnx/models/tree/main/vision/classification/densenet-121) |
|  | [densenet-7](https://github.com/onnx/models/tree/main/vision/classification/densenet-121) |
|  | [densenet-8](https://github.com/onnx/models/tree/main/vision/classification/densenet-121) |
|  | [densenet-9](https://github.com/onnx/models/tree/main/vision/classification/densenet-121) |
|  | [densenet-12](https://github.com/onnx/models/tree/main/vision/classification/densenet-121) |
| Efficientnet-lite4 | [efficientnet-lite4-11](https://github.com/onnx/models/tree/main/vision/classification/efficientnet-lite4) |
| Fast_neural_style | [candy-8](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [candy-9](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [mosaic-8](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [mosaic-9](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [pointilism-8](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [pointilism-9](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [rain-princess-8](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [rain-princess-9](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [udnie-8](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
|  | [udnie-9](https://github.com/onnx/models/tree/main/vision/style_transfer/fast_neural_style) |
| Googlenet | [googlenet-3](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/googlenet) |
|  | [googlenet-6](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/googlenet) |
|  | [googlenet-7](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/googlenet) |
|  | [googlenet-8](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/googlenet) |
|  | [googlenet-9](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/googlenet) |
|  | [googlenet-12](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/googlenet) |
| Inception_v1 | [inception-v1-6](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v1) |
|  | [inception-v1-7](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v1) |
|  | [inception-v1-8](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v1) |
|  | [inception-v1-9](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v1) |
|  | [inception-v1-12](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v1) |
| Inception_v2 | [inception-v2-7](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v2) |
|  | [inception-v2-8](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v2) |
|  | [inception-v2-9](https://github.com/onnx/models/tree/main/vision/classification/inception_and_googlenet/inception_v2) |
| Mnist | [mnist-7](https://github.com/onnx/models/tree/main/vision/classification/mnist) |
|  | [mnist-8](https://github.com/onnx/models/tree/main/vision/classification/mnist) |
|  | [mnist-12](https://github.com/onnx/models/tree/main/vision/classification/mnist) |
| Mobilenet | [mobilenetv2-7](https://github.com/onnx/models/tree/main/vision/classification/mobilenet) |
| Rcnn_ilsvrc13 | [rcnn-ilsvrc13-6](https://github.com/onnx/models/tree/main/vision/classification/rcnn_ilsvrc13) |
|  | [rcnn-ilsvrc13-7](https://github.com/onnx/models/tree/main/vision/classification/rcnn_ilsvrc13) |
|  | [rcnn-ilsvrc13-8](https://github.com/onnx/models/tree/main/vision/classification/rcnn_ilsvrc13) |
|  | [rcnn-ilsvrc13-9](https://github.com/onnx/models/tree/main/vision/classification/rcnn_ilsvrc13) |
| Resnet | [resnet18-v1-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet18-v2-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet34-v1-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet34-v2-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet50-caffe2-v1-6](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet50-caffe2-v1-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet50-caffe2-v1-8](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet50-caffe2-v1-9](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet50-v1-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet50-v1-12](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet50-v2-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet101-v1-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet101-v2-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet152-v1-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
|  | [resnet152-v2-7](https://github.com/onnx/models/tree/main/vision/classification/resnet) |
| Roberta | [roberta-base-11](https://github.com/onnx/models/tree/main/text/machine_comprehension/roberta) |
|  | [roberta-sequence-classification-9](https://github.com/onnx/models/tree/main/text/machine_comprehension/roberta) |
| Shufflenet | [shufflenet-6](https://github.com/onnx/models/tree/main/vision/classification/shufflenet) |
|  | [shufflenet-7](https://github.com/onnx/models/tree/main/vision/classification/shufflenet) |
|  | [shufflenet-8](https://github.com/onnx/models/tree/main/vision/classification/shufflenet) |
|  | [shufflenet-9](https://github.com/onnx/models/tree/main/vision/classification/shufflenet) |
|  | [shufflenet-v2-10](https://github.com/onnx/models/tree/main/vision/classification/shufflenet) |
|  | [shufflenet-v2-12](https://github.com/onnx/models/tree/main/vision/classification/shufflenet) |
| Squeezenet | [squeezenet1.0-3](https://github.com/onnx/models/tree/main/vision/classification/squeezenet) |
|  | [squeezenet1.0-6](https://github.com/onnx/models/tree/main/vision/classification/squeezenet) |
|  | [squeezenet1.0-7](https://github.com/onnx/models/tree/main/vision/classification/squeezenet) |
|  | [squeezenet1.0-8](https://github.com/onnx/models/tree/main/vision/classification/squeezenet) |
|  | [squeezenet1.0-9](https://github.com/onnx/models/tree/main/vision/classification/squeezenet) |
|  | [squeezenet1.0-12](https://github.com/onnx/models/tree/main/vision/classification/squeezenet) |
|  | [squeezenet1.1-7](https://github.com/onnx/models/tree/main/vision/classification/squeezenet) |
| Sub_pixel_cnn_2016 | [super-resolution-10](https://github.com/onnx/models/tree/main/vision/super_resolution/sub_pixel_cnn_2016) |
| Tiny-yolov2 | [tinyyolov2-7](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/tiny-yolov2) |
|  | [tinyyolov2-8](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/tiny-yolov2) |
| Tiny-yolov3 | [tiny-yolov3-11](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/tiny-yolov3) |
| Vgg | [vgg16-7](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg16-12](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg16-bn-7](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg19-7](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg19-bn-7](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg19-caffe2-6](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg19-caffe2-7](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg19-caffe2-8](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
|  | [vgg19-caffe2-9](https://github.com/onnx/models/tree/main/vision/classification/vgg) |
| Yolov3 | [yolov3-10](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/yolov3) |
|  | [yolov3-12](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/yolov3) |
| Zfnet-512 | [zfnet512-6](https://github.com/onnx/models/tree/main/vision/classification/zfnet-512) |
|  | [zfnet512-7](https://github.com/onnx/models/tree/main/vision/classification/zfnet-512) |
|  | [zfnet512-8](https://github.com/onnx/models/tree/main/vision/classification/zfnet-512) |
|  | [zfnet512-9](https://github.com/onnx/models/tree/main/vision/classification/zfnet-512) |
|  | [zfnet512-12](https://github.com/onnx/models/tree/main/vision/classification/zfnet-512) |
