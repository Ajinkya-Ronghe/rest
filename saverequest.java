private synchronized long getNextBatchId(String requestType, long currentTime, boolean isBatchEnabled) {
    if (isBatchEnabled) {
        long lastRequestTime = lastRequestTimes.getOrDefault(requestType, 0L);

        // Check if the current request is within the 5-second window
        if (currentTime - lastRequestTime <= BATCH_WINDOW_MS) {
            // Return the current batch ID from the map
            return currentBatchIds.getOrDefault(requestType, 1L);
        } else {
            // Fetch the latest batch ID from the database and increment it
            String query = "SELECT COALESCE(MAX(batch_id), 0) FROM staging_data WHERE req_name = :reqType";
            MapSqlParameterSource params = new MapSqlParameterSource().addValue("reqType", requestType);
            long currentBatchId = namedParameterJdbcTemplate.queryForObject(query, params, Long.class);

            // Increment the batch ID and return it
            long newBatchId = currentBatchId + 1;
            currentBatchIds.put(requestType, newBatchId);
            lastRequestTimes.put(requestType, currentTime);
            return newBatchId;
        }
    } else {
        // If batching is not enabled, return -1 or a default batch ID
        return -1L;  // Use -1 to represent no batching
    }
}
