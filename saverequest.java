package com.infy.ceh.management.repository;

import com.infy.ceh.management.util.QueryLoader;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.Timestamp;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class RequestRepositoryImpl implements RequestRepository {

    @Autowired
    private NamedParameterJdbcTemplate namedParameterJdbcTemplate;

    @Autowired
    private QueryLoader queryLoader;

    // To store the last request time and batch ID for each request type
    private ConcurrentHashMap<String, Long> lastRequestTimes = new ConcurrentHashMap<>();
    private ConcurrentHashMap<String, Long> currentBatchIds = new ConcurrentHashMap<>();

    private static final long BATCH_WINDOW_MS = 5000;  // 5 seconds in milliseconds

    @Override
    public void saveRequest(JSONObject requestBody) throws Exception {
        String requestType = requestBody.get("type").toString();
        boolean isBatchEnabled = checkBatchEnabled(requestType);

        long currentTime = System.currentTimeMillis();

        long batchId = getNextBatchId(requestType, currentTime, isBatchEnabled);

        try {
            String sql = queryLoader.getQuery("saveRequest");
            MapSqlParameterSource params = new MapSqlParameterSource()
                    .addValue("dataType", "json")
                    .addValue("reqName", requestType)
                    .addValue("jsonTextData", requestBody.get("json").toString())
                    .addValue("dataIdentifier", false)
                    .addValue("status", "P")
                    .addValue("batch", isBatchEnabled ? true : false)
                    .addValue("batch_id", batchId);

            namedParameterJdbcTemplate.update(sql, params);

        } catch (Exception e) {
            throw new Exception("Error saving request: " + e.getMessage(), e);
        }
    }

    /**
     * Check if batching is enabled for the given request type by querying the metadata_type table.
     * @param requestType The type of the incoming request.
     * @return True if batching is enabled, otherwise false.
     */
    private boolean checkBatchEnabled(String requestType) {
        String sql = "SELECT batch FROM metadata_type WHERE req_name = :reqName";
        MapSqlParameterSource params = new MapSqlParameterSource()
                .addValue("reqName", requestType);

        Boolean batchEnabled = namedParameterJdbcTemplate.queryForObject(sql, params, Boolean.class);
        return batchEnabled != null && batchEnabled;
    }

    /**
     * Get the next batch ID based on the current time and request type.
     * If batching is enabled, it assigns the previous batch ID if within the time window (5 seconds).
     * Otherwise, it increments the batch ID.
     * @param requestType The type of the request.
     * @param currentTime The current system time in milliseconds.
     * @param isBatchEnabled Whether batching is enabled for the request type.
     * @return The batch ID to use for this request.
     */
    private long getNextBatchId(String requestType, long currentTime, boolean isBatchEnabled) {
        // Check if batch is enabled for the type
        if (isBatchEnabled) {
            long lastRequestTime = lastRequestTimes.getOrDefault(requestType, 0L);

            // Check if the current request is within the 5-second window
            if (currentTime - lastRequestTime <= BATCH_WINDOW_MS) {
                // Return the current batch ID for this type
                return currentBatchIds.getOrDefault(requestType, 1L);
            } else {
                // Increment the batch ID and return it
                long newBatchId = currentBatchIds.getOrDefault(requestType, 1L) + 1;
                currentBatchIds.put(requestType, newBatchId);
                lastRequestTimes.put(requestType, currentTime);
                return newBatchId;
            }
        } else {
            // If batching is not enabled, return -1 or a default batch ID
            return null;
        }
    }
}
