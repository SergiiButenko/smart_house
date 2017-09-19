cd /var/www/
git reset --hard
git pull
msg=`git log -1 --pretty=%B | tr -s ' ' | tr ' ' '_'`

systemctl restart irrigation_7542.service
systemctl restart rules_handler.service
systemctl restart irrigation_viber_bot.service

echo 'HEAD is now '$msg