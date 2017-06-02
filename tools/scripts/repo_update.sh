cd /var/www/v2
git reset --hard
git pull
msg=`git log -1 --pretty=%B | tr -s ' ' | tr ' ' '_'`
sed -i "s|test|$msg|g" /var/www/v2/index.html
sed -i "s|test|$msg|g" /var/www/v2/beta.html
sed -i "s|test|$msg|g" /var/www/v2/python_code/static/index.html
echo 'HEAD is now '$msg