function changeImagePath(img) {
	if (img.src.match(/airmoving.gif/))
    	img.src = "../images/airmoving_static.gif";
	else if (img.src.match(/airmoving_static.gif/))
    	img.src = "../images/airmoving.gif";
   }