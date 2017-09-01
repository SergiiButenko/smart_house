var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
var branch = [];

$(document).ready(function() {
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
                    "<button class=\"dropdown-item\" type=\"button\" data-id="+item['id']+">"+item['name']+"</button>"
                    );
            }
        }
    });

    $(".dropdown-item").click(function() {
        id = $(this).data('id')
        
        default_time = branch[id]['default_time'] 
        default_interval = branch[id]['default_interval'] 
        default_time_wait = branch[id]['default_time_wait']


        console.log(id);
console.log(default_time);
console.log(default_interval);
console.log(default_time_wait);
console.log($(this).text());

        $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');

        card=$(".dropdown-item").closest(".card")
        card.data('id', id);
        card.find('#irrigation_minutes').val(1);
        card.find('#irrigation_intervals').val(1);
        card.find('#irrigation_time_wait').val(1);
});


    $("#add_rule_block").click(function() {
        element = $(".card_to_copy").children();
        $(".card-group").append(element.clone().show());
        $(".remove_card").click(function() {
            $(this).parent().parent().remove();
        });
    });

    $(".remove_card").click(function() {
        $(this).parent().parent().remove();
    });
});
