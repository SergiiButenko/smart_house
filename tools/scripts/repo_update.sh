cd /var/www
git reset --hard
git pull
version=`git rev-parse --short HEAD`
sed -n "s/test/$version/g" /var/www/index.html
/etc/init.d/apache2 reload