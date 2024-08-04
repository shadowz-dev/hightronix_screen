jQuery(document).ready(function ($) {
    const main = function () {
        $('.user-token-reveal').each(function() {
            updateTokenReveal($(this), false);
        });
    };

    $(document).on('click', '.user-add', function () {
        showModal('modal-user-add');
        $('.modal-user-add input[type=text]:eq(0)').focus().select();
    });

    $(document).on('click', '.user-edit', function () {
        const user = JSON.parse($(this).parents('.user-item:eq(0)').attr('data-entity'));
        showModal('modal-user-edit');
        $('.modal-user-edit input:visible:eq(0)').focus().select();
        $('#user-edit-enabled').prop('checked', user.enabled);
        $('#user-edit-username').val(user.username);
        $('#user-edit-id').val(user.id);
    });

    const updateTokenReveal = function($btn, revealState) {
        const $holder = $btn.parents('.user-item:eq(0)');
        const $input = $holder.find('.input-token:eq(0)');
        const $icon = $btn.find('i:eq(0)');
        const isActive = revealState !== undefined ? !revealState : $icon.hasClass('fa-eye-slash');

        if (isActive) {
            $icon.removeClass('fa-eye-slash').addClass('fa-eye');
            $btn.removeClass('btn-neutral').addClass('btn-other');
            $input.val($input.attr('data-private'));
        } else {
            $icon.removeClass('fa-eye').addClass('fa-eye-slash');
            $btn.removeClass('btn-other').addClass('btn-neutral');
            $input.val($input.attr('data-public'));
        }
    };

    $(document).on('click', '.user-token-reveal', function () {
        updateTokenReveal($(this));
    });

    main();
});