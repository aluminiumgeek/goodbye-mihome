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

    $(document).ready(function() {
        shuffle(bg_images)
        $.backstretch(bg_images, {duration: 5 * 60 * 1000, fade: 3500});

        for (sid in sensors_data) {
            var panel = $('[data-sid="' + sid + '"]');
            var canvas = $('<canvas id="' + sid + '" width="' + panel.width() + '" height="' + panel.height() + '"></canvas>');
            panel.append(canvas);

            var params = {
                type: 'line',
                options: {
                    title: {display: false},
                    legend: {display: false},
                    tooltip: {enabled: false},
                    elements: {point: {radius: 2}},
                    scales: {xAxes: [{display: false}], yAxes: [{display: false}]}
                },
                data: sensors_data[sid]
            };
            var chart = new Chart(canvas.get(0), params);
        }
    });
})(jQuery);
