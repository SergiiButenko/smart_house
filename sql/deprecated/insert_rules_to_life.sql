insert into life (line_id, rule_id, timer, date) select w.line_id, w.rule_id,current_date +  w.time, current_date from week_schedule as w where w.day_number = date_part('dow', now());

insert into life (line_id, rule_id, timer, date) select w.line_id, 2,current_date + w.time + w.interval*interval '1 minute', current_date from week_schedule as w where w.day_number = date_part('dow', now()) and w.rule_id = 1;
