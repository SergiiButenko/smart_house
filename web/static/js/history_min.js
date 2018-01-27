var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');

$(document).ready(function() {
    $(".card-rule").each(function() {
        form_text($(this))
    });
    set_events();
});


function form_text(el_in) {
    var card = $(el_in).closest('.top')

    var time = $(card).data('timer')
    var minutes = $(card).data('time')
    var interval = $(card).data('intervals')
    var time_wait = $(card).data('time_wait')

    $(card).find("#summary").html(
        'O ' + time + '.</br>' +
        interval + ' рази, по ' + minutes + ' хвилин, з інтервалом в ' + time_wait + ' хвилин'
    );
}


function set_events() {
    $('.active_true_false').off().change(function(e) {
        var switcher = $(e.target);

        var old_value = !($(switcher).prop("checked"));
        console.log(old_value);
        var returnVal = confirm("Ви впевненні?");
        console.log(returnVal);
        if (returnVal == false) {
            $(switcher).prop("checked", old_value);
            // $(switcher).val($(switcher).old_value);
            return;
        }

        var id = $(switcher).data('id')
        if (old_value == false) {
            $.ajax({
                url: '/activate_ongoing_rule',
                type: "get",
                data: {
                    'id': id
                },
                beforeSend: function(xhr, opts) {
                    set_status_spinner();
                },
                error: function(data) {
                    alert("Сталася помилка. Cпробуйте ще раз");
                },
                complete: function(data) {
                    set_status_ok();
                }
            });
        } else {
            $.ajax({
                url: '/deactivate_ongoing_rule',
                type: "get",
                data: {
                    'id': id
                },
                beforeSend: function(xhr, opts) {
                    set_status_spinner();
                },
                error: function(data) {
                    alert("Сталася помилка. Cпробуйте ще раз");
                },
                complete: function(data) {
                    set_status_ok();
                }
            });
        }
    });
}