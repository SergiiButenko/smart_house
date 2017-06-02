select * from life where timer>= now() and timer<=now()::date+1 order by date, timer desc
