private synchronized long getNextBatchId(String requestType, long currentTime, boolean isBatchEnabled) throws Exception {
    if (isBatchEnabled) {
        // Fetch the latest batch ID and last request time from the database
        String query = "SELECT COALESCE(MAX(batch_id), 0), COALESCE(MAX(last_request_time), 0) FROM staging_data WHERE req_name = :reqType";
        MapSqlParameterSource params = new MapSqlParameterSource().addValue("reqType", requestType);
        
        // Query to get both batch ID and last request time
        return namedParameterJdbcTemplate.query(query, params, rs -> {
            long currentBatchId = rs.getLong(1);  // Max batch_id
            long lastRequestTimeFromDb = rs.getLong(2);  // Max last_request_time (timestamp)

            // Check if the current request is within the 5-second window from the last request time in the database
            if (currentTime - lastRequestTimeFromDb <= BATCH_WINDOW_MS) {
                // Return the current batch ID
                return currentBatchId;
            } else {
                // Increment the batch ID if the request falls outside the 5-second window
                long newBatchId = currentBatchId + 1;

                // Update the last request time in the in-memory map for faster future lookups
                currentBatchIds.put(requestType, newBatchId);
                lastRequestTimes.put(requestType, currentTime);

                return newBatchId;
            }
        });
    } else {
        // If batching is not enabled, return -1 or a default batch ID
        return -1L;  // Use -1 to represent no batching
    }
}
