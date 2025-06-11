# Performance Considerations

* Real-time data acquisition requires sufficient system resources
* Large data streams may require SSD storage for optimal performance
* Memory usage scales with buffer sizes and visualization complexity. Visualization is kept efficient by only updating data streams for source that are actually visible
* Spikes may occur in the data if receive buffer is kept low in size due to filtering edge effects
* B210 devices work poorly with default frame sizes, which is why default receive frame size has been kept at 1024