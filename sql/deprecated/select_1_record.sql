select l.line_id, l.rule_id, l.timer from life as l where l.state = 0 order by date, timer, rule_id limit 1;
