class CCTVViewer
{
	constructor()
	{
		this.cctvViewerElement = document.getElementById("cctv-view-container");
		this.logListElement = document.getElementById('log-list');
		this.cctvViewElementList = [];
		this.cctvInfoList = [];
		this.notifyCam = [];
		this.log = [];
		this.mapMarkerList = [];

		fetch("/cctv.json").then((res) => res.json()).then((json) => {
			for(let cctv of json["cctvList"])
			{
				let cctvContainer = document.createElement("div");
				cctvContainer.classList.add("cctv-view");
				this.cctvViewElementList.push(cctvContainer);
				let cctvNameLabelElement = document.createElement("span");
				cctvNameLabelElement.classList.add("cctv-name-label");
				cctvNameLabelElement.innerText = cctv.name;
				cctvContainer.appendChild(cctvNameLabelElement);

				let cctvInfo = {"info":cctv};
				let showElement = undefined;
				switch(cctv.type)
				{
					case "image":
					showElement = document.createElement("img");
					showElement.src = cctv.targetPath + '&random=' + Math.random();
					cctvInfo["element"] = imgElement;
					cctvInfo["interval"] = setInterval(() => {
						showElement.src = cctv.targetPath + '&random=' + Math.random();
					},41);
					cctvContainer.appendChild(showElement);
					break;
					case "image_stream":
					showElement = document.createElement("img");
					showElement.src = cctv.targetPath + '&random=' + Math.random();
					cctvInfo["element"] = showElement;
					cctvContainer.appendChild(showElement);
					break;
					case "video":
					showElement = document.createElement("video");
					showElement.src = cctv.targetPath + '&random=' + Math.random();
					cctvInfo["element"] = showElement;
					cctvContainer.appendChild(showElement);
					break;
				}
				this.cctvInfoList.push(cctvInfo);

				this.cctvViewerElement.appendChild(cctvContainer);

				this.notifyCam.push({'interval':undefined,'timeout':undefined});
			}

			if(json['mapPath'] == 'navermap')
			{
				let naverMapScript = document.createElement('script');
				let mapElement = document.getElementById('map');
				mapElement.style = 'height:'+ mapElement.offsetWidth + 'px';
				naverMapScript.src = 'https://openapi.map.naver.com/openapi/v3/maps.js?ncpClientId=kbcszg1sco';
				
				document.head.appendChild(naverMapScript);
				naverMapScript.addEventListener('load', () => {
					let map = new naver.maps.Map(mapElement, {
						'zoom':1
					});

					let boundBox = new naver.maps.LatLngBounds();

					for(let cctv of json['cctvList'])
					{
						boundBox.extend(new naver.maps.LatLng({'x':cctv['location'][0],'y':cctv['location'][1]}));
						let marker = new naver.maps.Marker({
							'map':map,
							'position':{'x':cctv['location'][0],'y':cctv['location'][1]},
							'icon': {
								'path':{'x':0,'y':0},
								'style':'circle',
								'radius':3,
								'strokeWeight':6,
								'strokeColor':'blue',
							},
						});
						this.mapMarkerList.push(marker);
						marker.draw();
						map.fitBounds(boundBox);
					}
				});
			}
			else
			{
				let mapElement = document.getElementById('map');
				this.mapCanvasElement = document.getElementById('map-canvas');
				this.mapCanvasCtx = this.mapCanvasElement.getContext("2d");
				let mapImg = new Image();
				mapImg.addEventListener('load',() => {
					console.log(mapImg);
					console.log(mapElement.offsetWidth);
					this.mapCanvasElement.width = mapElement.offsetWidth;
					this.mapCanvasElement.height = mapImg.height / mapImg.width * mapElement.offsetWidth;
					this.mapCanvasCtx.drawImage(mapImg,0,0,this.mapCanvasElement.width,this.mapCanvasElement.height);

					for(let cctv of json['cctvList'])
					{
						let x = this.mapCanvasElement.width * cctv['location'][0];
						let y = this.mapCanvasElement.height * cctv['location'][1];

						this.mapCanvasCtx.beginPath();
						this.mapCanvasCtx.arc(x,y,5,0,2 * Math.PI);
						this.mapCanvasCtx.fillStyle = "blue";
						this.mapCanvasCtx.fill();
					}
				});
				mapImg.src = json['mapPath'];
			}
		}).catch((e) => {
			console.log(e);
			console.log("fetch cctv data error");
		});

		this.statusPooling = setInterval(() => {
			fetch('/status').then(res => res.json()).then(json => {
				let now = new Date();
				let timestamp = now.getFullYear() + '-' + (now.getMonth()+1) + '-' + now.getDate() + ' ' + now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
				for(const cam in json)
				{
					if(json[cam].length > 0)
					{
						for(const result of json[cam])
						{
							let logElement = document.createElement('div');
							let timeElement = document.createElement('span');
							timeElement.innerText = timestamp;
							logElement.appendChild(timeElement);

							let logString = this.cctvInfoList[cam]['info']['name'] + ': ' + result;
							let infoElement = document.createElement('div');
							if(typeof result == "string")
								infoElement.innerText = logString;
							logElement.appendChild(infoElement);
							let isLogBottom = this.logListElement.scrollTop + this.logListElement.clientHeight == this.logListElement.scrollHeight;
							this.logListElement.appendChild(logElement);
							if(isLogBottom)
								this.logListElement.scrollTo(0,this.logListElement.scrollHeight - this.logListElement.clientHeight);
						}

						if(!this.notifyCam[cam]['interval'])
						{
							this.notifyCam[cam]['interval'] = setInterval(() => {
								this.cctvViewElementList[cam].classList.toggle('notification');

								if(this.mapMarkerList.length)
								{
									let icon = this.mapMarkerList[cam].getIcon();
									icon['strokeColor'] = 'red';
									this.mapMarkerList[cam].setIcon(icon);
								}
								else
								{
									let x = this.mapCanvasElement.width * this.cctvInfoList[cam]['info']['location'][0];

									let y = this.mapCanvasElement.height * this.cctvInfoList[cam]['info']['location'][1];

									this.mapCanvasCtx.beginPath();
									this.mapCanvasCtx.arc(x,y,5,0,2 * Math.PI);
									this.mapCanvasCtx.fillStyle = "red";
									this.mapCanvasCtx.fill();

								}
							},500);
						}
						if(this.notifyCam[cam]['timeout'])
							clearTimeout(this.notifyCam[cam]['timeout']);

						this.notifyCam[cam]['timeout'] = setTimeout(() => {
							this.cctvViewElementList[cam].classList.remove('notification');
							clearInterval(this.notifyCam[cam]['interval']);
							this.notifyCam[cam]['interval'] = undefined;
							this.notifyCam[cam]['timeout'] = undefined;

							if(this.mapMarkerList.length)
							{
								let icon = this.mapMarkerList[cam].getIcon();
								icon['strokeColor'] = 'blue';
								this.mapMarkerList[cam].setIcon(icon);
							}
							else
							{
								let x = this.mapCanvasElement.width * this.cctvInfoList[cam]['info']['location'][0];

								let y = this.mapCanvasElement.height * this.cctvInfoList[cam]['info']['location'][1];

								this.mapCanvasCtx.beginPath();
								this.mapCanvasCtx.arc(x,y,5,0,2 * Math.PI);
								this.mapCanvasCtx.fillStyle = "blue";
								this.mapCanvasCtx.fill();
							}
						},5000);
					}
				}
			});
		},300);
	}
}

function inhibitSleep()
{
	let videoData = 'GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQJChYECGFOAZwEAAAAAAAIQEU2bdLpNu4tTq4QVSalmU6yBoU27i1OrhBZUrmtTrIHYTbuMU6uEElTDZ1OsggEtTbuMU6uEHFO7a1OsggH67AEAAAAAAABZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVSalmsirXsYMPQkBNgI1MYXZmNTkuMTYuMTAwV0GNTGF2ZjU5LjE2LjEwMESJiEDDiAAAAAAAFlSua9CuAQAAAAAAAEfXgQFzxYhlQe1LfTkm/pyBACK1nIN1bmSIgQCGhVZfVlA5g4EBI+ODhQJUC+QA4AEAAAAAAAAQsIEFuoEFmoECVbCEVbmBARJUw2dAnXNzAQAAAAAAACdjwIBnyAEAAAAAAAAaRaOHRU5DT0RFUkSHjUxhdmY1OS4xNi4xMDBzcwEAAAAAAABiY8CLY8WIZUHtS305Jv5nyAEAAAAAAAAlRaOHRU5DT0RFUkSHmExhdmM1OS4xOC4xMDAgbGlidnB4LXZwOWfIokWjiERVUkFUSU9ORIeUMDA6MDA6MTAuMDAwMDAwMDAwAAAfQ7Z1peeBAKOggQAAgIJJg0IAAEAARgA4JBwYSgAAICAAEb///4r+AAAcU7trkbuPs4EAt4r3gQHxggHQ8IED';
	let videoElement = document.createElement('video');
	videoElement.setAttribute('loop','true');
	videoElement.setAttribute('style','display:none');
	let sourceElement = document.createElement('source');
	sourceElement.src = 'data:webm;base64,' + videoData;
	videoElement.appendChild(sourceElement);
	document.body.appendChild(videoElement);
	videoElement.play();
	document.body.removeEventListener('click',inhibitSleep);
}

document.body.addEventListener('click',inhibitSleep);

window.addEventListener("load",() => {
	cctv = new CCTVViewer();
});
