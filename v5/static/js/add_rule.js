var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
var branch = [];

$(document).ready(function() {
    add_to_date = get_parameter_by_name('add_to_date');
    add_cards = (add_to_date != null)

    //Rename branches
    $.ajax({
        url: server + '/branches_names',
        success: function(data) {
            list = data['list']            
            list = list.sort((function (a, b) { 
                              return new Date(a.start_time) - new Date(b.start_time)
                            }));
            for (j in list) {
                item = list[j]

                branch[item['id']] = {
                    'name': item['name'],
                    'default_time': parseInt(item['default_time']),
                    'default_interval': parseInt(item['default_interval']),
                    'default_time_wait': parseInt(item['default_time_wait']),
                    'start_time': new Date(item['start_time'])
                }

                $(".dropdown-menu-card").append(
                    "<button class=\"dropdown-item\" data-id=" + item['id'] + ">" + item['name'] + "</button>"
                );

                if (add_cards) {
                    if (item['id'] == 17) {
                        continue;
                    }

                    default_time = branch[item['id']]['default_time']
                    default_interval = branch[item['id']]['default_interval']
                    default_time_wait = branch[item['id']]['default_time_wait']
                    default_time_start = branch[item['id']]['start_time']
                    default_date_start = convert_date_to_local_date(add_to_date);

                    card = clone_card();

                    card.find('.card').data('id', item['id']);
                    card.find("#dropdownMenu2").html(branch[item['id']]['name'] + ' <span class="caret"></span>');
                    card.find('.irrigation_minutes').val(default_time);
                    card.find('.irrigation_intervals').val(default_interval);
                    card.find('.irrigation_time').val(convert_date_to_time(default_time_start));
                    card.find('.irrigation_date').val(default_date_start);
                    group = card.find('#irrigation_time_wait_group')
                    if (default_interval <= 1 || isNaN(default_interval)) {
                        group.hide();
                    } else {
                        group.show();
                    }
                    card.find('.irrigation_time_wait').val(default_time_wait);
                }
            }

            if (!add_cards) {
                clone_card();
            }

            $(".dropdown-item").click(function() {
                drop_down_click(this);
            });

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

            $(".remove_card").click(function() {
                $(this).parent().parent().parent().remove();
            });

        }

    });

    $("#add_rule_block").click(function() {
        clone_card();
    });

    function clone_card() {
        element = $(".card_to_copy").children();
        clone = element.clone();
        $(".card-group").append(clone.show());

        $(".remove_card").click(function() {
            $(this).parent().parent().parent().remove();
        });

        $(".dropdown-item").click(function() {
            drop_down_click(this);
        });

        return clone;
    }


    function drop_down_click(el) {
        id = $(el).data('id')

        default_time = branch[id]['default_time']
        default_interval = branch[id]['default_interval']
        default_time_wait = branch[id]['default_time_wait']
        default_time_start = branch[id]['start_time']

        $(el).parents(".dropdown").find('.btn').html($(el).text() + ' <span class="caret"></span>');

        card = $(el).closest(".card")
        card.data('id', id);
        card.find('.irrigation_minutes').val(default_time);
        card.find('.irrigation_intervals').val(default_interval);
        console.log(card.find('.irrigation_time'))
        card.find('.irrigation_time').val(convert_date_to_time(default_time_start));

        group = card.find('#irrigation_time_wait_group')
        if (default_interval <= 1 || isNaN(default_interval)) {
            group.hide();
        } else {
            group.show();
        }

        card.find('.irrigation_time_wait').val(default_time_wait);
    }

    $("#go_plan").click(function() {

        json = { 'list': {} }

        $(".card").each(function() {
            if ($(this).data('id') == 0) {
                return;
            }

            id = $(this).data('id');
            time = $(this).find('.irrigation_minutes').val();
            interval = $(this).find('.irrigation_intervals').val();
            time_wait = $(this).find('.irrigation_time_wait').val();
            date_start = $(this).find('.irrigation_date').val();
            time_start = $(this).find('.irrigation_time').val();
            json.list[id] = {
                "time": time,
                "interval": interval,
                "time_wait": time_wait,
                "date_start": date_start,
                "time_start": time_start
            }
        });

        console.log(json);

    });



});