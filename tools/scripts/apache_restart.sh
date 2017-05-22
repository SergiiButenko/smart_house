cd /var/www
git reset --hard
git pull
version=`git rev-parse --short HEAD`
msg=`git log -1 --pretty=%B | tr -s ' ' | tr ' ' '_'`
sed -i "s|test|$msg|g" /var/www/index.html
echo 'HEAD is now '$msg
/etc/init.d/apache2 reload