var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
var branch = [];

$(document).ready(function() {

    $('.irrigation_intervals').on('input', function(e) {
        var input = parseInt($(this).val());
        card = $(this).closest(".card")
        group = card.find('#irrigation_time_wait_group')
        if (input <= 1 || isNaN(input)) {
            group.hide();
        } else {
            group.show();
        }
    });

    //Rename branches
    $.ajax({
        url: server + '/branches_names',
        success: function(data) {
            list = data['list']
            for (j in list) {
                item = list[j]
                branch[item['id']] = {
                    'name': item['name'],
                    'default_time': parseInt(item['default_time']) || 10,
                    'default_interval': parseInt(item['default_interval']) || 2,
                    'default_time_wait': parseInt(item['default_time_wait']) || 15
                }

                $(".dropdown-menu").append(
                    "<button class=\"dropdown-item\" data-id=" + item['id'] + ">" + item['name'] + "</button>"
                );
            }

            $(".dropdown-item").click(function() {
                drop_down_click(this);
            });
        }
    });

    $("#add_rule_block").click(function() {
        element = $(".card_to_copy").children();
        $(".card-group").append(element.clone().show());

        $(".remove_card").click(function() {
            $(this).parent().parent().remove();
        });

        $(".dropdown-item").click(function() {
            drop_down_click(this);
        });
    });

    $(".remove_card").click(function() {
        $(this).parent().parent().remove();
    });

    function drop_down_click(el) {
        id = $(el).data('id')

        default_time = branch[id]['default_time']
        default_interval = branch[id]['default_interval']
        default_time_wait = branch[id]['default_time_wait']

        $(el).parents(".dropdown").find('.btn').html($(el).text() + ' <span class="caret"></span>');

        card = $(el).closest(".card")
        card.data('id', id);
        card.find('.irrigation_minutes').val(default_time);
        card.find('.irrigation_intervals').val(default_interval);
        group = card.find('#irrigation_time_wait_group')
        if (default_interval <= 1 || isNaN(default_interval)) {
            group.hide();
        } else {
            group.show();
        }

        card.find('.irrigation_time_wait').val(default_time_wait);
    }

    $("#go_plan").click(function() {
      
       json = {'list':{}}

        $(".card").each(function() {
            if ($(this).data('id') == 0){
                return;
            }

            id = $(this).data('id');
            time = $(this).find('.irrigation_minutes').val();
            interval = $(this).find('.irrigation_intervals').val();
            time_wait = $(this).find('.irrigation_time_wait').val();
            json.list[id]={"time": time, "interval": interval, "time_wait": time_wait}
        });
       
       console.log(json);

    });



});