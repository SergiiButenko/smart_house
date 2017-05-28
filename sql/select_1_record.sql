select distinct on (l.date) l.line_id, l.timer  from life as l where l.state = 0 order by date, timer;
