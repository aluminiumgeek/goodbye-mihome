(function() {
    function shuffle(a) {
        var j, x, i;
        for (i = a.length; i; i--) {
            j = Math.floor(Math.random() * i);
            x = a[i - 1];
            a[i - 1] = a[j];
            a[j] = x;
        }
    }

    function create_chart(sid) {
        if (window.charts[sid]) {
            window.charts[sid].destroy();
        }
        var panel = $('[data-sid="' + sid + '"]');
        var canvas = $('<canvas id="' + sid + '" width="' + panel.width() + '" height="' + panel.height() + '"></canvas>');
        panel.append(canvas);

        var params = {
            type: 'line',
            options: {
                animation: false,
                title: {display: false},
                legend: {display: false},
                tooltip: {enabled: false},
                elements: {point: {radius: 2}},
                scales: {xAxes: [{display: false}], yAxes: [{display: false}]}
            },
            data: sensors_data[sid]
        };
        window.charts[sid] = new Chart(canvas.get(0), params);
    }

    $(document).ready(function() {
        shuffle(bg_images)
        $.backstretch(bg_images, {duration: 5 * 60 * 1000, fade: 3500});

        window.charts = {}
        for (sid in sensors_data) {
            create_chart(sid);
        }

        var updatesSocket = new WebSocket('ws://' + window.location.host + '/updates');
        updatesSocket.onmessage = function(event) {
            var data = JSON.parse(event.data);
            if (data.sensor == 'sensor_ht') {
                var t = data.temperature.split('.');
                var h = data.humidity.split('.');
                var panel = $('[data-sid="' + data.sid + '"]');
                panel.find('.temperature .main').text(t[0]);
                panel.find('.temperature .decimal').text(t[1]);
                panel.find('.humidity .main').text(h[0]);
                panel.find('.humidity .decimal').text(h[1]);

                sensors_data[data.sid]['datasets'][0]['data'].push(data.temperature);
                sensors_data[data.sid]['datasets'][1]['data'].push(data.humidity);
                sensors_data[data.sid]['datasets'][0]['data'].shift();
                sensors_data[data.sid]['datasets'][1]['data'].shift();
                create_chart(data.sid);
            }
        }
    });
})(jQuery);
