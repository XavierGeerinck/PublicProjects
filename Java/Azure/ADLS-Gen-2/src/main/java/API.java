import com.microsoft.azure.storage.blob.*;
import com.microsoft.azure.storage.blob.models.BlockBlobUploadResponse;
import com.microsoft.rest.v2.http.HttpPipeline;
import com.squareup.okhttp.*;
import com.sun.org.apache.xml.internal.security.exceptions.Base64DecodingException;
import io.reactivex.Flowable;
import io.reactivex.Single;
import okio.Buffer;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.MalformedURLException;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class API {
    private final String accessKey;
    private final String storageUrlBase;
    private final String storageAccountName;
    private final String storageContainer;
    private final OkHttpClient httpClient;

    // https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create
    private final static String STORAGE_SERVICE_VERSION = "2018-11-09";

    // https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create
    // http://www.vogella.com/tutorials/JavaLibrary-OkHttp/article.html
    // http://square.github.io/okhttp/
    public API(String storageAccountName, String storageContainer, String accessKey) {
        this.accessKey = accessKey;
        this.storageAccountName = storageAccountName;
        this.storageContainer = storageContainer;
        this.storageUrlBase = String.format("https://%s.dfs.core.windows.net", storageAccountName);
//        this.storageUrlBase = String.format("https://%s.blob.core.windows.net", storageAccountName);
        this.httpClient = new OkHttpClient();
    }

    public String getStorageUrlBase() {
        return storageUrlBase;
    }

    public String createFile(String filePath) {
        MediaType BINARY = MediaType.parse("application/octet-stream");
        RequestBody body = RequestBody.create(BINARY, "");

        Request request = new Request.Builder()
                .header("x-ms-date", getDate())
                .header("x-ms-version", STORAGE_SERVICE_VERSION)
                .url(this.storageUrlBase + "/" + this.storageContainer + filePath + "?resource=file")
                .put(body)
                .build();

        System.out.println(this.storageUrlBase + "/" + this.storageContainer + filePath + "?resource=file");

        // Add our signature
        Request requestWithAuthorization = addSignature(request, getDate(), STORAGE_SERVICE_VERSION);

        Response response;

        try {
            response = this.httpClient.newCall(requestWithAuthorization).execute();
            System.out.println(response.body().string());
        } catch (IOException e) {
            e.printStackTrace();
            return "";
        }

        return response.toString();
    }

    public String appendDataToFile(String filePath, int offset, byte[] content) {
        MediaType BINARY = MediaType.parse("application/octet-stream");
        RequestBody body = RequestBody.create(BINARY, content);

        Request request = new Request.Builder()
                .header("x-ms-date", getDate())
                .header("x-ms-version", STORAGE_SERVICE_VERSION)
                .url(this.storageUrlBase + "/" + this.storageContainer + filePath + "?action=append&position=" + offset)
                .patch(body)
                .build();

        // Add our signature
        Request requestWithAuthorization = addSignature(request, getDate(), STORAGE_SERVICE_VERSION);

        Response response;

        try {
            response = this.httpClient.newCall(requestWithAuthorization).execute();
            System.out.println(response.body().string());
        } catch (IOException e) {
            e.printStackTrace();
            return "";
        }

        return response.toString();
    }

    public String flushDataToFile(String filePath, int offset) {
        MediaType BINARY = MediaType.parse("application/octet-stream");
        RequestBody body = RequestBody.create(BINARY, "");

        Request request = new Request.Builder()
                .header("x-ms-date", getDate())
                .header("x-ms-version", STORAGE_SERVICE_VERSION)
                .url(this.storageUrlBase + "/" + this.storageContainer + filePath + "?action=flush&position=" + offset)
                .patch(body)
                .build();

        // Add our signature
        Request requestWithAuthorization = addSignature(request, getDate(), STORAGE_SERVICE_VERSION);

        Response response;

        try {
            response = this.httpClient.newCall(requestWithAuthorization).execute();
            System.out.println(response.body().string());
        } catch (IOException e) {
            e.printStackTrace();
            return "";
        }

        return response.toString();
    }

    public String getDate() {
        SimpleDateFormat fmt = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss");
        fmt.setTimeZone(TimeZone.getTimeZone("GMT"));
        return fmt.format(Calendar.getInstance().getTime()) + " GMT";
    }

    private Request addSignature(Request request, String date, String serviceVersion) {
        String path = request.httpUrl().encodedPath();
        String stringToSign = buildStringToSign(request, path, date, serviceVersion);
        String encryptedSignature = this.createAuthorizationHeader(stringToSign);

        return request.newBuilder().header("Authorization", "SharedKey " + this.storageAccountName + ":" + encryptedSignature).build();
    }

    // requestMethod = "PUT"
    // https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create
    // https://docs.microsoft.com/en-us/rest/api/apimanagement/apimanagementrest/azure-api-management-rest-api-authentication
    // https://docs.microsoft.com/en-us/rest/api/storageservices/authorize-with-shared-key
    // https://tsmatz.wordpress.com/2016/07/06/how-to-get-azure-storage-rest-api-authorization-header/
    // https://github.com/Azure/azure-storage-java/blob/21ed0379eaadcf849eb7795be3716aa1b9a4a375/microsoft-azure-storage/src/com/microsoft/azure/storage/core/SharedAccessSignatureHelper.java
    private String buildStringToSign(Request request, String filePath, String date, String version) {
        StringBuilder sb = new StringBuilder();
        sb.append(request.method().toUpperCase() + '\n'); // Method
        sb.append('\n'); // Content-Encoding
        sb.append('\n'); // Content-Language


        try {
            if (request.body().contentLength() == 0) {
                sb.append('\n'); // Content-Length
            } else {
                sb.append(String.valueOf(request.body().contentLength()) + '\n'); // Content-Length
            }
        } catch (IOException e) {
            e.printStackTrace();
        }


        sb.append('\n'); // Content-MD5
        sb.append(request.body().contentType().toString() + '\n'); // Content-Type
        sb.append('\n'); // Date (empty since x-ms-date is expected)
        sb.append('\n'); // If-Modified-Since
        sb.append('\n'); // If-Match
        sb.append('\n'); // If-None-Match
        sb.append('\n'); // If-Unmodified-Since
        sb.append('\n'); // Range

        // CanonicalizedResource
        sb.append(buildCanonicalizedHeaders(request));
        sb.append(buildCanonicalizedResource(request));

        return sb.toString();
    }

    private String buildCanonicalizedResource(Request request) {
        StringBuilder sb = new StringBuilder();

        sb.append("/");
        sb.append(this.storageAccountName);
        sb.append(request.httpUrl().encodedPath());

        if (request.httpUrl().query() != null) {
            Map<String, String> queryParams = new HashMap<>();

            // Add Headers from request that start with x-ms- to new hashset
            for (int i = 0; i < request.httpUrl().querySize(); i++) {
                String queryParamName = request.httpUrl().queryParameterName(i);
                String queryParamValue = request.httpUrl().queryParameterValue(i);

                queryParams.put(queryParamName.toLowerCase(), queryParamValue);
            }

            // Sort those headers based on the name
            queryParams = new TreeMap<>(queryParams);

            // Add those as a string
            for (String key : queryParams.keySet()) {
                sb.append('\n' + key + ":" + queryParams.get(key));
            }

            // @todo: should implement concatenating list of values with , in the query value
        }

        return sb.toString();
    }

    // https://docs.microsoft.com/en-us/rest/api/storageservices/authorize-with-shared-key#Constructing_Element
    private String buildCanonicalizedHeaders(Request request) {
        Map<String, String> headers = new HashMap<>();

        // Add Headers from request that start with x-ms- to new hashset
        for (int i = 0; i < request.headers().size(); i++) {
            String headerName = request.headers().name(i);
            String headerValue = request.headers().value(i);

            if (!headerName.startsWith("x-ms-")) {
                continue;
            }

            headers.put(headerName.toLowerCase(), headerValue);
        }

        // Sort those headers based on the name
        headers = new TreeMap<>(headers);

        // Add those as a string
        StringBuilder sb = new StringBuilder();

        for (String key : headers.keySet()) {
            sb.append(key + ":" + headers.get(key) + '\n');
        }

        // @todo: should implement concatenating list of values with , in the header value

        return sb.toString();
    }

    private String createAuthorizationHeader(String canonicalizedString) {
        return HMAC_SHA256(canonicalizedString, this.accessKey);
    }

    public String HMAC_SHA256(String toGetHash, String secret) {
        String authKey = "";

        try {

            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(Base64.getDecoder().decode(secret), "HmacSHA256"));
            authKey = new String(Base64.getEncoder().encode(mac.doFinal(toGetHash.getBytes(StandardCharsets.UTF_8))));

        } catch (Exception e) {
            System.out.println("Error: " + e.toString());
        }

        return authKey;
    }
}
