#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Optional, Union

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

from cfg import auth #cfg.py: auth=('username','$GITHUB_SEC')

app=FastAPI()
requests=AsyncClient()
templates=Jinja2Templates(directory='rms')
app.mount('/static',StaticFiles(directory='rms/static'),name='static')


@dataclass
class assetFile:
    name:str
    url:str
    urlCN:str

    def __repr__ (self) -> str:
        return '[{}]({}) [[CN] {}]({})'.format(self.name,self.url,self.name,self.urlCN)

class SoftWare:
    repo:str
    update_time:str
    release:str
    body:str
    assets:list[assetFile]

    # init from json
    def __init__(self,repo,json:dict[dict,list,str]):
        self.repo=repo
        self.update_time=json['published_at']
        self.release=json['tag_name']
        self.body='<p>'+('</p><p>'.join(json['body'].splitlines()))+'</p>'
        self.assets=list()
        assets:list[dict[str,Union[str,int,dict]]]=json['assets']
        for asset in assets:
            assetfile=assetFile(asset['name'],asset['browser_download_url'],'https://ghproxy.com/'+asset['browser_download_url'])
            # print(assetfile)
            self.assets.append(assetfile)
    
    def __repr__(self) -> str:
        return 'REPO={} , UPDATE AT={} , RELEASE={} , ASSETS={}'.format(self.repo,self.update_time,self.release,' '.join([str(i) for i in self.assets]))

class SoftwareManager:
    source_list:list[str]
    scheduler:AsyncIOScheduler
    softs:Optional[dict[str,SoftWare]]

    def __init__(self,repos:list[str],**scheduler_cfg) -> None:
        self.source_list=repos
        self.scheduler=AsyncIOScheduler()
        self.softs=dict()
        self.job=self.scheduler.add_job(self.update,'interval',**scheduler_cfg)
        self.scheduler.start()
    
    async def update(self) -> None:
        print('get_updates')
        softs=await self.get_updates(self.source_list)
        self.softs.update(softs)
        # self.printAll()

    def printAll(self) -> None:
        # print(self.softs)
        for repo in self.softs:
            print(self.softs[repo])
            # print()

    def getAll(self) -> Optional[dict[str,SoftWare]]:
        return self.softs

    async def get_updates(self,repos:list[str]) -> Optional[dict[str,SoftWare]]:
        ret:dict[Optional[SoftWare]]={}
        for repo in repos:
            print('GET latest release for ',repo)
            repo_upd=await self.get_update(repo=repo)
            if repo_upd != None:
                ret[repo]=repo_upd
        return ret

    async def get_update(self,repo:str) -> Optional[SoftWare]:
        url='https://api.github.com/repos/{}/releases/latest'.format(repo)
        req=await requests.get(url=url,auth=auth)
        try:
            j=req.json()
            ret=SoftWare(repo,j)
            print('Success to get release for',repo)
            return ret
        except Exception as e:
            print('Faild to get release for',repo)
            print('Reason',e)
            return

sources=["2dust/v2rayN", "2dust/v2rayNG", "Notsfsssf/pixez-flutter", "huanghongxun/HMCL", "Mrs4s/go-cqhttp", "thpatch/thtk", "fatedier/frp"]
manager=SoftwareManager(sources,minutes=1,timezone="Asia/Shanghai")

@app.get("/")
async def root(request:Request):
    # print(manager.getAll())
    return templates.TemplateResponse(
        'softwares.html',
        {
            'title':'软件库',
            'request':request,
            'softs':manager.getAll()
        }
    )

if __name__=='__main__':
    uvicorn.run(app='main:app',host='0.0.0.0',port=11996,reload=True)
