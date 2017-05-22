cd /var/www
git reset --hard
git pull
msg=`git log -1 --pretty=%B | tr -s ' ' | tr ' ' '_'`
sed -i "s|test|$msg|g" /var/www/index.html
echo 'HEAD is now '$msg