package com.example.wuziqi;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import okhttp3.*;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.concurrent.CompletableFuture;

public class OpenAIApiClient {
    private static final String TAG = "OpenAIApiClient";
    private final String apiKey;
    private final String baseUrl;
    private final String modelName;
    private final GameEngine gameEngine;
    private final OkHttpClient client;

    public OpenAIApiClient(String apiKey, String baseUrl, String modelName, GameEngine gameEngine) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.modelName = modelName;
        this.gameEngine = gameEngine;
        this.client = new OkHttpClient();
    }

    public void getAIMove(int[][] board, int boardSize, LLMResponseCallback callback) {
        // Construct the board string
        StringBuilder boardStr = new StringBuilder();
        for (int i = 0; i < boardSize; i++) {
            for (int j = 0; j < boardSize; j++) {
                if (board[i][j] == 0) {
                    boardStr.append(".");
                } else if (board[i][j] == 1) {
                    boardStr.append("X"); // Player stone
                } else {
                    boardStr.append("O"); // AI stone
                }
                if (j < boardSize - 1) {
                    boardStr.append(" ");
                }
            }
            boardStr.append("\n");
        }

        // Construct the prompt
        String prompt = String.format(
            "你是一个世界顶级五子棋AI，执白子'O'，对手是'X'。\n" +
            "棋盘大小：%dx%d，坐标从0开始。\n\n" +
            "【当前棋盘】\n%s\n\n" +
            "【你的任务】\n轮到你下，请输出最佳落子位置（格式：row,col），并遵循以下规则：\n\n" +
            "🎯 决策顺序（必须优先考虑）：\n" +
            "1. ❗ 防守：如果对手下一步能形成\"活四\"或\"双三\"，必须立即阻挡！\n" +
            "2. ✅ 攻击：如果你能形成\"活四\"或\"冲四+活三\"，优先进攻取胜。\n" +
            "3. 🔄 攻防兼备：如果某个位置既能阻止对手，又能建立自己的进攻线路，优先选择它。\n" +
            "4. ⚠️ 斜线同样重要！不要忽略对角线威胁。\n\n" +
            "📌 示例：\n" +
            "- 如果 X 有活四，你必须挡。\n" +
            "- 如果你下在某点，既可堵住 X 的活三，又可形成自己的活三 → 这是最佳选择。\n" +
            "- 不要只想着\"我不能输\"，而要思考\"我能赢\"。\n\n" +
            "⚠️ 注意：\n" +
            "- 绝不能忽略对手的\"活三\"！\n" +
            "- 输出格式：只返回一行 \"row,col\"，例如 \"7,7\"\n" +
            "- 不要解释，不要多说话。",
            boardSize, boardSize, boardStr.toString()
        );

        // Create the request body
        JSONObject requestBody = new JSONObject();
        try {
            requestBody.put("model", modelName);
            requestBody.put("temperature", 0.1);
            requestBody.put("max_tokens", 32);
            requestBody.put("n", 1);

            JSONArray messages = new JSONArray();
            JSONObject systemMessage = new JSONObject();
            systemMessage.put("role", "system");
            systemMessage.put("content", "你是专业五子棋AI，冷静、精准、防守严密，只输出 row,col。");
            messages.put(systemMessage);

            JSONObject userMessage = new JSONObject();
            userMessage.put("role", "user");
            userMessage.put("content", prompt);
            messages.put(userMessage);

            requestBody.put("messages", messages);
        } catch (JSONException e) {
            Log.e(TAG, "Error creating request body: " + e.getMessage());
            callback.onError("Error creating request: " + e.getMessage());
            return;
        }

        Request request = new Request.Builder()
            .url(baseUrl)
            .post(RequestBody.create(requestBody.toString(), MediaType.get("application/json")))
            .addHeader("Authorization", "Bearer " + apiKey)
            .addHeader("Content-Type", "application/json")
            .build();

        client.newCall(request).enqueue(new okhttp3.Callback() {
            @Override
            public void onFailure(okhttp3.Call call, IOException e) {
                Log.e(TAG, "API request failed: " + e.getMessage());
                // Run on main thread to update UI
                new Handler(Looper.getMainLooper()).post(() -> {
                    callback.onError("API request failed: " + e.getMessage());
                });
            }

            @Override
            public void onResponse(okhttp3.Call call, okhttp3.Response response) throws IOException {
                String responseBody = response.body().string();
                Log.d(TAG, "API response: " + responseBody);

                if (response.isSuccessful()) {
                    try {
                        // Parse the response
                        JSONObject responseJson = new JSONObject(responseBody);
                        JSONArray choices = responseJson.getJSONArray("choices");
                        String aiResponse = choices.getJSONObject(0).getJSONObject("message").getString("content").trim();

                        Log.d(TAG, "AI response: " + aiResponse);

                        // Parse the coordinates from the response
                        String cleaned = aiResponse.replaceAll("\\s", "").replaceAll("[()]", "");
                        if (cleaned.contains(",")) {
                            String[] parts = cleaned.split(",");
                            if (parts.length == 2) {
                                int r = Integer.parseInt(parts[0]);
                                int c = Integer.parseInt(parts[1]);
                                if (r >= 0 && r < boardSize && c >= 0 && c < boardSize && board[r][c] == 0) {
                                    Log.d(TAG, "Parsed AI move: (" + r + ", " + c + ")");
                                    // Run on main thread to update UI
                                    new Handler(Looper.getMainLooper()).post(() -> {
                                        callback.onSuccess(r, c);
                                    });
                                    return;
                                }
                            }
                        }

                        // Run on main thread to update UI
                        new Handler(Looper.getMainLooper()).post(() -> {
                            callback.onError("AI response format invalid: " + aiResponse);
                        });
                    } catch (JSONException e) {
                        Log.e(TAG, "Error parsing response: " + e.getMessage());
                        // Run on main thread to update UI
                        new Handler(Looper.getMainLooper()).post(() -> {
                            callback.onError("Error parsing API response: " + e.getMessage());
                        });
                    }
                } else {
                    Log.e(TAG, "API request failed with code: " + response.code());
                    // Run on main thread to update UI
                    new Handler(Looper.getMainLooper()).post(() -> {
                        callback.onError("API request failed with code: " + response.code());
                    });
                }
                response.close();
            }
        });
    }

    public interface LLMResponseCallback {
        void onSuccess(int row, int col);
        void onError(String error);
    }
}