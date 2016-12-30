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
    
    function get_images_list() {
        var images = []
        $('.bg-image').each(function(item) {
            images.push('/static/img/bg/' + $('.bg-image:eq(' + item + ')').data('bg'));
        });
        shuffle(images);
        return images;
    }
    
    function update() {
        $.ajax({
            url: '/',
        }).done(function(page) {
            var data_html = $(page).find('.row.ht').html();
            $('.row.ht').html(data_html)ж
        })
    }
    
    $(document).ready(function() {
        $.backstretch(get_images_list(), {duration: 5 * 60 * 1000, fade: 3500});
        setInterval(update, 60 * 1000);
    });
})(jQuery);
