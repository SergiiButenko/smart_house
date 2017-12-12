cd /var/www/
git reset --hard
git pull origin master
msg=`git log -1 --pretty=%B | tr -s ' ' | tr ' ' '_'`

cd /var/www/services
cp -uv * /etc/systemd/system/

systemctl daemon-reload

systemctl restart irrigation_7542.service
systemctl restart rules_handler.service
#systemctl restart irrigation_viber_bot.service
systemctl restart irrigation_power_supply.service

echo 'HEAD is now '$msg