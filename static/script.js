// Automatically set current date and time on load
window.onload = function() {
    const now = new Date();
    document.getElementById('date').value = now.toISOString().split('T')[0];
    document.getElementById('time').value = now.toTimeString().split(' ')[0].slice(0, 5);
    updateChart(); // Auto-generate the chart
};

// Update Chart Function
function updateChart() {
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;

    if (!date || !time) {
        console.error('Date and time are required.');
        alert('Please select both date and time!');
        return;
    }

    const [year, month, day] = date.split('-');
    const [hour, minute] = time.split(':');

    fetch('/chart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            year: parseInt(year),
            month: parseInt(month),
            day: parseInt(day),
            hour: parseInt(hour),
            minute: parseInt(minute)
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('chart').src = 'data:image/png;base64,' + data.chart;
    })
    .catch(error => {
        console.error('Error fetching chart:', error);
        alert(`Failed to fetch chart: ${error.message}`);
    });
}
