import os

def w(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created: {path}")

w("app/src/main/java/com/tai1233444/MainActivity.java", """package com.tai1233444;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.widget.FrameLayout;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.core.ImageProxy;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.google.common.util.concurrent.ListenableFuture;
import java.nio.ByteBuffer;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
public class MainActivity extends AppCompatActivity {
    private PreviewView previewView;
    private CursorView cursorView;
    private ExecutorService cameraExecutor;
    private static final int PERMISSION_CODE = 100;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(0xFF000000);
        cursorView = new CursorView(this);
        FrameLayout.LayoutParams cp = new FrameLayout.LayoutParams(-1,-1);
        root.addView(cursorView, cp);
        previewView = new PreviewView(this);
        previewView.setScaleType(PreviewView.ScaleType.FILL_CENTER);
        int pw = dpToPx(140), ph = dpToPx(190);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(pw, ph);
        lp.gravity = android.view.Gravity.BOTTOM | android.view.Gravity.START;
        lp.setMargins(dpToPx(12), 0, 0, dpToPx(12));
        previewView.setAlpha(0.85f);
        root.addView(previewView, lp);
        setContentView(root);
        cameraExecutor = Executors.newSingleThreadExecutor();
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            startCamera();
        } else {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, PERMISSION_CODE);
        }
    }
    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> future = ProcessCameraProvider.getInstance(this);
        future.addListener(() -> {
            try {
                ProcessCameraProvider provider = future.get();
                Preview preview = new Preview.Builder().build();
                preview.setSurfaceProvider(previewView.getSurfaceProvider());
                ImageAnalysis analysis = new ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST).build();
                analysis.setAnalyzer(cameraExecutor, imageProxy -> processImage(imageProxy));
                CameraSelector selector = new CameraSelector.Builder()
                    .requireLensFacing(CameraSelector.LENS_FACING_FRONT).build();
                provider.unbindAll();
                provider.bindToLifecycle(this, selector, preview, analysis);
            } catch (Exception e) { e.printStackTrace(); }
        }, ContextCompat.getMainExecutor(this));
    }
    private void processImage(ImageProxy imageProxy) {
        try {
            ByteBuffer yBuffer = imageProxy.getPlanes()[0].getBuffer();
            ByteBuffer uBuffer = imageProxy.getPlanes()[1].getBuffer();
            ByteBuffer vBuffer = imageProxy.getPlanes()[2].getBuffer();
            int width = imageProxy.getWidth(), height = imageProxy.getHeight();
            float[] center = findSkinCenter(yBuffer, uBuffer, vBuffer, width, height);
            if (center != null) {
                int sw = getResources().getDisplayMetrics().widthPixels;
                int sh = getResources().getDisplayMetrics().heightPixels;
                float sx = (1f - center[0]) * sw, sy = center[1] * sh;
                runOnUiThread(() -> cursorView.updateCursor(sx, sy, true));
            } else { runOnUiThread(() -> cursorView.updateCursor(0, 0, false)); }
        } finally { imageProxy.close(); }
    }
    private float[] findSkinCenter(ByteBuffer yBuf, ByteBuffer uBuf, ByteBuffer vBuf, int w, int h) {
        byte[] yArr = new byte[yBuf.remaining()];
        byte[] uArr = new byte[uBuf.remaining()];
        byte[] vArr = new byte[vBuf.remaining()];
        yBuf.get(yArr); uBuf.get(uArr); vBuf.get(vArr);
        long sumX=0, sumY=0, count=0;
        for (int j=0; j<h; j++) {
            for (int i=0; i<w; i++) {
                int yVal = yArr[j*w+i] & 0xFF;
                int uIdx = (j/2)*(w/2)+(i/2);
                int uVal = (uIdx<uArr.length)?(uArr[uIdx]&0xFF)-128:0;
                int vVal = (uIdx<vArr.length)?(vArr[uIdx]&0xFF)-128:0;
                if (yVal>80 && uVal>-20 && uVal<20 && vVal>10 && vVal<40) { sumX+=i; sumY+=j; count++; }
            }
        }
        if (count>500) return new float[]{(float)sumX/count/w, (float)sumY/count/h};
        return null;
    }
    private int dpToPx(int dp) { return Math.round(dp * getResources().getDisplayMetrics().density); }
    @Override
    public void onRequestPermissionsResult(int code, @NonNull String[] p, @NonNull int[] r) {
        super.onRequestPermissionsResult(code, p, r);
        if (code==PERMISSION_CODE && r.length>0 && r[0]==PackageManager.PERMISSION_GRANTED) startCamera();
    }
    @Override protected void onDestroy() { super.onDestroy(); cameraExecutor.shutdown(); }
}""")

w("app/src/main/java/com/tai1233444/CursorView.java", """package com.tai1233444;
import android.content.Context;
import android.graphics.*;
import android.view.View;
public class CursorView extends View {
    private float cursorX=500, cursorY=500;
    private boolean visible=false;
    private Paint fillPaint, ringPaint, dotPaint;
    public CursorView(Context context) {
        super(context);
        setLayerType(LAYER_TYPE_HARDWARE, null);
        fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        fillPaint.setColor(0xCCFFFFFF);
        fillPaint.setStyle(Paint.Style.FILL);
        fillPaint.setShadowLayer(18,0,0,0xFF00FFFF);
        ringPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        ringPaint.setColor(0xFF00FFFF);
        ringPaint.setStyle(Paint.Style.STROKE);
        ringPaint.setStrokeWidth(3f);
        dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        dotPaint.setColor(0xFF00FFFF);
        dotPaint.setStyle(Paint.Style.FILL);
    }
    public void updateCursor(float x, float y, boolean show) {
        visible=show;
        if(show){ cursorX=cursorX+(x-cursorX)*0.25f; cursorY=cursorY+(y-cursorY)*0.25f; }
        invalidate();
    }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if(!visible) return;
        canvas.drawCircle(cursorX,cursorY,22,fillPaint);
        canvas.drawCircle(cursorX,cursorY,36,ringPaint);
        canvas.drawCircle(cursorX,cursorY,5,dotPaint);
    }
}""")

w("app/src/main/AndroidManifest.xml", """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.tai1233444">
    <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="33"/>
    <uses-permission android:name="android.permission.CAMERA"/>
    <uses-feature android:name="android.hardware.camera" android:required="true"/>
    <application android:allowBackup="true" android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name" android:theme="@style/Theme.HandGesture">
        <activity android:name=".MainActivity" android:exported="true"
            android:screenOrientation="portrait">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>""")

w("app/src/main/res/values/strings.xml", """<?xml version="1.0" encoding="utf-8"?>
<resources><string name="app_name">Hand Gesture</string></resources>""")

w("app/src/main/res/values/themes.xml", """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.HandGesture" parent="Theme.AppCompat.Light.NoActionBar">
        <item name="colorPrimary">#000000</item>
        <item name="colorPrimaryDark">#000000</item>
        <item name="colorAccent">#00FFFF</item>
        <item name="android:windowBackground">#000000</item>
    </style>
</resources>""")

w("app/build.gradle", """plugins { id 'com.android.application' }
android {
    compileSdk 33
    defaultConfig {
        applicationId "com.tai1233444"
        minSdk 24
        targetSdk 33
        versionCode 1
        versionName "1.0"
    }
    buildTypes { release { minifyEnabled false } }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}
dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
    implementation 'androidx.camera:camera-core:1.3.1'
    implementation 'androidx.camera:camera-camera2:1.3.1'
    implementation 'androidx.camera:camera-lifecycle:1.3.1'
    implementation 'androidx.camera:camera-view:1.3.1'
    implementation 'com.google.guava:guava:31.0.1-android'
}""")

w("build.gradle", """buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:7.4.2' }
}
allprojects { repositories { google(); mavenCentral() } }""")

w("settings.gradle", """pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "HandGesture"
include ':app'""")

w("gradle/wrapper/gradle-wrapper.properties", """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-7.5-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists""")

print("ALL DONE!")