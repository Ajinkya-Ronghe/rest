private synchronized long getNextBatchId(String requestType, long currentTime, boolean isBatchEnabled) throws Exception {
    if (isBatchEnabled) {
        // Fetch the latest batch ID and last created_date (used as last request time) from the database
        String query = "SELECT COALESCE(MAX(batch_id), 0) AS max_batch_id, COALESCE(MAX(EXTRACT(EPOCH FROM created_date)), 0) AS last_request_time FROM staging_data WHERE req_name = :reqType";
        MapSqlParameterSource params = new MapSqlParameterSource().addValue("reqType", requestType);

        return namedParameterJdbcTemplate.query(query, params, rs -> {
            if (rs.next()) {
                long currentBatchId = rs.getLong("max_batch_id");  // Max batch_id
                long lastRequestTimeFromDb = rs.getLong("last_request_time");  // Max created_date as UNIX timestamp

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
            } else {
                // No previous requests found, start with batch ID 1
                return 1L;
            }
        });
    } else {
        // If batching is not enabled, return -1 or a default batch ID
        return -1L;  // Use -1 to represent no batching
    }
}
