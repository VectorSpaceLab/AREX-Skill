# Alternate Clients and Toolchains

This page is reference-only. The repo contains several non-Python client and deployment examples, but they need external toolchains and are not bundled as runnable helpers in the generated skill.

## Java / Scala / Spark

Evidence:

- `java_predict_client/README.md`
- `java_predict_client/pom.xml`
- `java_predict_client/src/main/java/com/tobe/client/DensePredictClient.java`
- `java_predict_client/src/main/java/com/tobe/client/SparsePredictClient.java`
- `java_predict_client/src/main/scala/com/tobe/client/ScalaDensePredictClient.scala`
- `java_predict_client/src/main/scala/com/tobe/client/SparkDensePredictClient.scala`
- `java_predict_client/src/main/scala/com/tobe/data/GenerateDenseTfrecords.scala`
- `java_predict_client/src/main/scala/com/tobe/data/GenerateSparseTfrecords.scala`

What the repo shows:

- Maven is used for dense/sparse gRPC clients.
- Scala clients are thin wrappers around the Java client.
- Spark examples generate TFRecords and are tied to a Spark/Hadoop environment.
- The README examples assume local or cluster-based infrastructure that is outside the generated skill's runtime scope.

Why reference-only:

- Requires Maven, Scala, and often Spark/Hadoop classpaths.
- The Spark paths point at HDFS and cluster-style execution.
- The generated skill should not depend on local generated protobuf sources or a checked-out service tree.

## Go

Evidence:

- `golang_predict_client/README.md`
- `golang_predict_client/src/generate_proto_files.sh`

What the repo shows:

- A Go gRPC client with protobuf generation steps.
- The setup assumes a Go toolchain and `protoc` plugins.

Why reference-only:

- Requires a Go toolchain and protobuf generation.
- The client is useful for understanding request shapes, but not for bundled runtime execution here.

## C++

Evidence:

- `cpp_predict_server/README.md`
- `cpp_predict_client/README.md`
- `cpp_predict_client/sparse_predict_client.cc`
- `cpp_predict_client/generate_proto_files/generate_proto_files.sh`

What the repo shows:

- A TensorFlow Serving server binary and a Bazel-based C++ client.
- The client is built in the TensorFlow Serving source tree and depends on generated protos.

Why reference-only:

- Requires Bazel and a TensorFlow Serving build or binary.
- The generated skill should not assume access to the upstream TensorFlow Serving source tree.

## Android

Evidence:

- `android_client/app/src/main/java/com/tobe/androidclient/MainActivity.java`
- `android_client/app/build.gradle`
- `android_client/app/src/main/AndroidManifest.xml`

What the repo shows:

- An on-device TensorFlow inference demo using the Android TensorFlow interface.
- The example expects Android Studio / Gradle and native Android build tooling.

Why reference-only:

- Requires Android SDK, Gradle, and a mobile build environment.
- Not part of the generated runtime skill's Python execution scope.

## iOS

Evidence:

- `ios_client/README.md`
- `ios_client/AppDelegate.mm`
- `ios_client/RunModelViewController.mm`
- `ios_client/ios_image_load.mm`
- `ios_client/Podfile`

What the repo shows:

- An Objective-C++ iOS demo that loads a TensorFlow model locally.
- The flow depends on CocoaPods and Xcode project files.

Why reference-only:

- Requires Xcode, CocoaPods, and iOS build tooling.
- It is a platform-specific demo, not a reusable Python helper.

## When to use this page

Use this page when the user asks about one of the alternate deployment/client surfaces, especially if they want to understand the request shape or the build toolchain without actually building it in the current environment.
