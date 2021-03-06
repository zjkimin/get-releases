#!/usr/bin/env python3
#兼容3.10以下
from dataclasses import dataclass
from datetime import datetime

import markdown
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

import cfg  # cfg.py: see cfg_temp.py

app=FastAPI()
requests=AsyncClient()
templates=Jinja2Templates(directory='rms')
app.mount(cfg.path+'static',StaticFiles(directory='rms/static'),name='static')


@dataclass
class assetFile:
    name:str
    size:int
    url:str
    urlCN:str
    def get_size(self) -> int:
        return self.size

    @staticmethod
    def __size_hum_convert(value) -> str:
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024.0
        for i in range(len(units)):
            if (value / size) < 1:
                return "%.2f%s" % (value, units[i])
            value = value / size
    
    def get_size_hum(self) -> str:
        return self.__size_hum_convert(self.get_size())

    def __repr__ (self) -> str:
        return '[{}]({}) [[CN] {}]({})'.format(self.name,self.url,self.name,self.urlCN)

class SoftWare:
    repo:str
    update_time:str
    update_timestamp:int
    release:str
    body:str
    beta:bool
    assets:list

    # init from json
    def __init__(self,repo,json):
        self.repo=repo
        self.update_time=json['published_at']
        self.update_timestamp=datetime.strptime(self.update_time,'%Y-%m-%dT%H:%M:%SZ').timestamp().__int__()
        self.release=json['tag_name']
        self.beta=json['prerelease']
        self.body='<p>'+('</p><p>'.join(markdown.markdown(json['body']).splitlines()))+'</p>'
        self.assets=list()
        assets=json['assets']
        for asset in assets:
            assetfile=assetFile(asset['name'],asset['size'],asset['browser_download_url'],'https://ghproxy.com/'+asset['browser_download_url'])
            # print(assetfile)
            self.assets.append(assetfile)
    
    def __repr__(self) -> str:
        return 'REPO={} , UPDATE AT={} , RELEASE={} , ASSETS={}'.format(self.repo,self.update_time,self.release,' '.join([str(i) for i in self.assets]))

class SoftwareManager:
    source_list:list
    scheduler:AsyncIOScheduler
    softs:dict

    def __init__(self,repos:list,**scheduler_cfg) -> None:
        self.source_list=repos
        self.scheduler=AsyncIOScheduler()
        self.softs=dict()
        self.job=self.scheduler.add_job(self.update,'interval',**scheduler_cfg)
        self.scheduler.start()
    
    async def update(self) -> None:
        print('get_updates')
        softs=await self.get_updates(self.source_list)
        updated=sorted(softs.items(),key=lambda soft: soft[1].update_timestamp,reverse=True)
        self.softs.update(updated)
        # self.printAll()

    def printAll(self) -> None:
        # print(self.softs)
        for repo in self.softs:
            print(self.softs[repo])
            # print()

    def getAll(self):
        return self.softs

    async def get_updates(self,repos:list):
        ret={}
        for repo in repos:
            print('GET latest release for ',repo)
            repo_upd=await self.get_update(repo=repo)
            if repo_upd != None:
                ret[repo]=repo_upd
        return ret

    async def get_update(self,repo:str):
        url='https://api.github.com/repos/{}/releases'.format(repo)
        req=await requests.get(url=url,auth=cfg.auth)
        try:
            j=req.json()[0]
            ret=SoftWare(repo,j)
            print('Success to get release for',repo)
            return ret
        except Exception as e:
            print('Faild to get release for',repo)
            print('Reason',e)
            return

manager=SoftwareManager(cfg.sources,minutes=1,timezone="Asia/Shanghai")

@app.get(cfg.path)
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
    uvicorn.run(app='main_comp:app',host='0.0.0.0',port=cfg.port,reload=True)
