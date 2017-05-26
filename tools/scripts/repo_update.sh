cd /var/www/v2
git reset --hard
git pull
msg=`git log -1 --pretty=%B | tr -s ' ' | tr ' ' '_'`
sed -i "s|test|$msg|g" /var/www/index.html
sed -i "s|test|$msg|g" /var/www/beta.html
echo 'HEAD is now '$msg

systemctl restart irrigation_backend.service