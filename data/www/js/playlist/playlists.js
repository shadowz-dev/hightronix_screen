jQuery(document).ready(function ($) {

    const main = function () {
        const $qrcode = $('#qrcode');

        if ($qrcode.length) {
            new QRCode($qrcode.get(0), {
                text: $qrcode.attr('data-qrcode-payload'),
                width: 128,
                height: 128,
                colorDark: '#222',
                colorLight: '#fff',
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    };

    $(document).on('click', '.playlist-add', function () {
        showModal('modal-playlist-add');
        $('.modal-playlist-add input:eq(0)').focus().select();
    });

    $(document).on('click', '.playlist-preview', function () {
        const $icon = $(this).find('i');
        const isPlay = $icon.hasClass('fa-play');
        const $holder = $(this).parents('.preview:eq(0)');

        if (isPlay) {
            const $iframe = $('<iframe>', {
                src: $(this).attr('data-url'),
                frameborder: 0
            });

            $holder.append($iframe);
            $(this).addClass('hover-only');
            $icon.removeClass('fa-play').addClass('fa-pause');
        } else {
            $holder.find('iframe').remove();
            $(this).removeClass('hover-only');
            $icon.removeClass('fa-pause').addClass('fa-play');
        }
    });

    $(document).on('click', '.cast-scan', function () {
        showModal('modal-playlist-cast-scan');
        const $modal = $('.modal-playlist-cast-scan:visible');
        const $holder = $modal.find('.cast-devices');
        const $loading = $modal.find('.loading');

        $loading.removeClass('hidden');
        $holder.removeClass('hidden');
        $holder.html('');
        $loading.html($loading.attr('data-loading'));

        $.ajax({
            method: 'GET',
            url: route_cast_scan,
            headers: {'Content-Type': 'application/json'},
            success: function (response) {
                $loading.addClass('hidden')

                for (let i = 0; i < response.devices.length; i++) {
                    const device = response.devices[i];
                    $holder.append($('<li><a href="javascript:void(0)" class="cast-device" data-id="' + device.friendly_name + '"><i class="fa fa-brands fa-chromecast"></i>' + device.friendly_name + '</a></li>'));
                }
            }
        });
    });

    $(document).on('click', '.cast-device', function () {
        const $modal = $('.modal-playlist-cast-scan:visible');
        const $holder = $modal.find('.cast-devices');
        const $loading = $modal.find('.loading');

        $holder.addClass('hidden');
        $loading.removeClass('hidden');
        $loading.html($loading.attr('data-casting'));

        const id = $(this).attr('data-id');

        $.ajax({
            url: route_cast_url,
            method: 'POST',
            data: JSON.stringify({
                device: id,
                url: $('#playlist-preview-url').val()
            }),
            headers: {'Content-Type': 'application/json'},
            success: function (response) {
                $loading.addClass('hidden');
                hideModal();
            },
            error: function () {
                $loading.addClass('hidden');
                $holder.removeClass('hidden');
            }
        });
    });

    main();
});
