package com.lungnet.app;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private WebView mWebView;
    private View mLayoutLoading;
    private View mLayoutError;
    private EditText mEditServerUrl;
    private TextView mTextErrorDetail;
    private Button mBtnSaveConnect;
    private Button mBtnRetry;

    private ValueCallback<Uri[]> mUploadMessage;
    private final static int FILECHOOSER_RESULTCODE = 1;
    private SharedPreferences mPrefs;
    private String mCurrentUrl;

    private static final String PREF_NAME = "lungnet_prefs";
    private static final String KEY_SERVER_URL = "server_url";
    private static final String DEFAULT_URL = "https://oncofusion-ai.streamlit.app";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mPrefs = getSharedPreferences(PREF_NAME, MODE_PRIVATE);
        mCurrentUrl = mPrefs.getString(KEY_SERVER_URL, DEFAULT_URL);

        // Bind layouts
        mWebView = findViewById(R.id.webview);
        mLayoutLoading = findViewById(R.id.layout_loading);
        mLayoutError = findViewById(R.id.layout_error);
        mEditServerUrl = findViewById(R.id.edit_server_url);
        mTextErrorDetail = findViewById(R.id.text_error_detail);
        mBtnSaveConnect = findViewById(R.id.btn_save_connect);
        mBtnRetry = findViewById(R.id.btn_retry);

        mEditServerUrl.setText(mCurrentUrl);

        // Setup WebView
        setupWebView();

        // Listeners
        mBtnSaveConnect.setOnClickListener(v -> {
            String newUrl = mEditServerUrl.getText().toString().trim();
            if (!newUrl.startsWith("http://") && !newUrl.startsWith("https://")) {
                newUrl = "http://" + newUrl;
            }
            mCurrentUrl = newUrl;
            mPrefs.edit().putString(KEY_SERVER_URL, mCurrentUrl).apply();
            mEditServerUrl.setText(mCurrentUrl);
            loadUrl(mCurrentUrl);
        });

        mBtnRetry.setOnClickListener(v -> loadUrl(mCurrentUrl));

        // Start load
        loadUrl(mCurrentUrl);
    }

    private void setupWebView() {
        WebSettings settings = mWebView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);

        // Required to keep app loading inside the WebView
        mWebView.setWebViewClient(new WebViewClient() {
            private boolean mHasError = false;

            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                mHasError = false;
                showLoading();
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (!mHasError) {
                    showWebView();
                }
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                // If it is the main frame, display error layout
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    if (request.isForMainFrame()) {
                        mHasError = true;
                        showError(error.getDescription().toString());
                    }
                }
            }

            @SuppressWarnings("deprecation")
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) {
                    mHasError = true;
                    showError(description);
                }
            }
        });

        mWebView.setWebChromeClient(new WebChromeClient() {
            // Override file chooser for Streamlit file uploads
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (mUploadMessage != null) {
                    mUploadMessage.onReceiveValue(null);
                }
                mUploadMessage = filePathCallback;

                Intent contentSelectionIntent = new Intent(Intent.ACTION_GET_CONTENT);
                contentSelectionIntent.addCategory(Intent.CATEGORY_OPENABLE);
                contentSelectionIntent.setType("*/*");

                Intent chooserIntent = new Intent(Intent.ACTION_CHOOSER);
                chooserIntent.putExtra(Intent.EXTRA_INTENT, contentSelectionIntent);
                chooserIntent.putExtra(Intent.EXTRA_TITLE, "Select Patient CT Scan");

                try {
                    startActivityForResult(chooserIntent, FILECHOOSER_RESULTCODE);
                } catch (ActivityNotFoundException e) {
                    mUploadMessage = null;
                    Toast.makeText(MainActivity.this, "Cannot open file chooser", Toast.LENGTH_LONG).show();
                    return false;
                }
                return true;
            }
        });
    }

    private void loadUrl(String url) {
        mWebView.loadUrl(url);
    }

    private void showLoading() {
        mLayoutLoading.setVisibility(View.VISIBLE);
        mWebView.setVisibility(View.GONE);
        mLayoutError.setVisibility(View.GONE);
    }

    private void showWebView() {
        mLayoutLoading.setVisibility(View.GONE);
        mWebView.setVisibility(View.VISIBLE);
        mLayoutError.setVisibility(View.GONE);
    }

    private void showError(String details) {
        mLayoutLoading.setVisibility(View.GONE);
        mWebView.setVisibility(View.GONE);
        mLayoutError.setVisibility(View.VISIBLE);
        mTextErrorDetail.setText("Error details: " + details);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent intent) {
        super.onActivityResult(requestCode, resultCode, intent);
        if (requestCode == FILECHOOSER_RESULTCODE) {
            if (null == mUploadMessage) return;
            Uri[] result = null;
            if (resultCode == RESULT_OK && intent != null) {
                String dataString = intent.getDataString();
                if (dataString != null) {
                    result = new Uri[]{Uri.parse(dataString)};
                } else if (intent.getClipData() != null) {
                    int count = intent.getClipData().getItemCount();
                    result = new Uri[count];
                    for (int i = 0; i < count; i++) {
                        result[i] = intent.getClipData().getItemAt(i).getUri();
                    }
                }
            }
            mUploadMessage.onReceiveValue(result);
            mUploadMessage = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (mWebView.getVisibility() == View.VISIBLE && mWebView.canGoBack()) {
            mWebView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
