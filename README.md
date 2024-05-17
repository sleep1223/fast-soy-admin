<!-- markdownlint-disable MD033 MD041 -->

<p align="center">
  <a href="https://github.com/sleep1223/"><img src="web/public/favicon.svg" width="200" height="200" alt="github"></a>
</p>

<div align="center">

# FastSoyAdmin
<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->

[![license](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![github stars](https://img.shields.io/github/stars/sleep1223/fast-soy-admin)](https://github.com/sleep1223/fast-soy-admin)
[![github forks](https://img.shields.io/github/forks/sleep1223/fast-soy-admin)](https://github.com/sleep1223/fast-soy-admin)

![python](https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=edb641)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg?logo=python&logoColor=edb641)](https://github.com/psf/black)
[![pyright](https://img.shields.io/badge/types-pyright-797952.svg?logo=python&logoColor=edb641)](https://github.com/Microsoft/pyright)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


<span><a href="./README.en.md">English</a> | 中文</span>

</div>

> [!NOTE]
> 如果您觉得 `FastSoyAdmin` 对您有所帮助，或者您喜欢我们的项目，请在 GitHub 上给我们一个 ⭐️。您的支持是我们持续改进和增加新功能的动力！感谢您的支持！

## 简介

[`FastSoyAdmin`](https://github.com/sleep1223/fast-soy-admin) 是一个现代且功能强大的后台管理模板，采用最新的技术栈，前端使用 Vue3、Vite5、TypeScript、Pinia 和 UnoCSS。后端采用 FastAPI、Pydantic 和 Tortoise ORM，并提供完善的 ApiFox 在线文档。它内置丰富的主题配置和组件，代码规范严谨，实现了自动化的文件路由系统。`FastSoyAdmin` 为您提供一站式的后台管理解决方案，开箱即用，同时也是快速学习前沿技术的最佳实践。

## 特性

- **前沿技术应用**：后端采用 FastAPI, Pydantic, Tortoise ORM, 前端采用 Vue3, Vite5, TypeScript, Pinia 和 UnoCSS 等最新流行的技术栈。
- **独特的权限控制**：后端实现了独特的权限控制，前后端用户角色权限严格分离。
- **详细的日志管理**：基于[`SoybeanAdmin`](https://github.com/sleep1223/fast-soy-admin)，结合实际业务需求，新增了日志管理和API权限控制功能，实现了后端权限的二次验证。
- **后端集成大量实用工具**：代码耦合度低，并重写了部分实用函数。
- **清晰的项目架构**：采用 pnpm monorepo 架构，结构清晰，优雅易懂。
- **严格的代码规范**：前端遵循 [SoybeanJS 规范](https://docs.soybeanjs.cn/zh/standard)，集成了eslint, prettier 和 simple-git-hooks，后端使用 [Ruff](https://docs.astral.sh/ruff/) 和 [Pyright](https://microsoft.github.io/pyright), 保证代码的规范性。
- **TypeScript**： 支持严格的类型检查，提高代码的可维护性。
- **丰富的主题配置**：内置多样的主题配置，与 UnoCSS 完美结合。
- **内置国际化方案**：轻松实现多语言支持。
- **丰富的页面组件**：内置多样页面和组件，包括403、404、500页面，以及布局组件、标签组件、主题配置组件等。
- **命令行工具**：内置高效的命令行工具，git提交、删除文件、发布等。
- **移动端适配**：完美支持移动端，实现自适应布局。


## 相关

- [预览地址](https://fast-soy-admin2.sleep0.de/)
- [项目文档](https://sleep1223.github.io/fast-soy-admin-docs/zh/)
- [Apifox文档](https://apifox.com/apidoc/shared-7cd78102-46eb-4701-88b1-3b49c006504b)
- [Github 仓库](https://github.com/sleep1223/fast-soy-admin)
- [SoybeanAdmin](https://gitee.com/honghuangdc/soybean-admin)

## 示例图片

![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-01.png)
![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-02.png)

![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-04.png)

![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-06.png)
![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-07.png)
![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-08.png)

![](https://raw.githubusercontent.com/sleep1223/fast-soy-admin-docs/51832d41f1d951bd9d61a9bcfdf137deb81fd3c5/src/assets/QQ%E6%88%AA%E5%9B%BE20240517223056.jpg)
![](https://raw.githubusercontent.com/sleep1223/fast-soy-admin-docs/51832d41f1d951bd9d61a9bcfdf137deb81fd3c5/src/assets/QQ%E6%88%AA%E5%9B%BE20240517223123.jpg)

![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-09.png)
![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-10.png)
![](https://soybeanjs-1300612522.cos.ap-guangzhou.myqcloud.com/uPic/soybean-admin-v1-mobile.png)


## 使用

**环境准备**

确保你的环境满足以下要求：

- **git**: 你需要使用 git 来克隆和管理项目版本。
- **python**: >= 3.10
- **NodeJS**: >=18.0.0，推荐 18.19.0 或更高。
- **pnpm**: >= 8.0.0，推荐最新版本。

**克隆项目**

```bash
git clone https://github.com/sleep1223/fast-soy-admin
```

**安装依赖**

```bash
pdm install 或者 poery install
cd web && pnpm i
```
> 由于本项目采用了 pnpm monorepo 的管理方式，因此请不要使用 npm 或 yarn 来安装依赖。

**启动项目**

前端
```bash
pnpm dev
```

后端
```bash
pdm run run.py 或者 poetry run run.py
```

**构建项目**

```bash
pnpm build
```


## 如何贡献

我们热烈欢迎并感谢所有形式的贡献。如果您有任何想法或建议，欢迎通过提交 [pull requests](https://github.com/sleep1223/fast-soy-admin/pulls) 或创建 GitHub [issue](https://github.com/sleep1223/fast-soy-admin/issues/new) 来分享。

## Git 提交规范

本项目已内置 `commit` 命令，您可以通过执行 `pnpm commit` 来生成符合 [Conventional Commits]([conventionalcommits](https://www.conventionalcommits.org/)) 规范的提交信息。在提交PR时，请务必使用 `commit` 命令来创建提交信息，以确保信息的规范性。


## 浏览器支持

推荐使用最新版的 Chrome 浏览器进行开发，以获得更好的体验。

| [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/archive/internet-explorer_9-11/internet-explorer_9-11_48x48.png" alt="IE" width="24px" height="24px"  />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/edge/edge_48x48.png" alt=" Edge" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/firefox/firefox_48x48.png" alt="Firefox" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/chrome/chrome_48x48.png" alt="Chrome" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/safari/safari_48x48.png" alt="Safari" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) |
| --- | --- | --- | --- | --- |
| not support | last 2 versions | last 2 versions | last 2 versions | last 2 versions |

## 开源作者

[Sleep1223](https://github.com/Sleep1223)


## 贡献者

感谢以下贡献者的贡献。如果您想为本项目做出贡献，请参考 [如何贡献](#如何贡献)。

<a href="https://github.com/sleep1223/fast-soy-admin/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=sleep1223/fast-soy-admin" />
</a>

## 交流

`FastSoyAdmin` 是完全开源免费的项目，在帮助开发者更方便地进行中大型管理系统开发，同时也提供微信和 QQ 交流群，使用问题欢迎在群内提问。


![QQ交流群](https://raw.githubusercontent.com/sleep1223/fast-soy-admin-docs/51832d41f1d951bd9d61a9bcfdf137deb81fd3c5/src/assets/qqgroup.jpg)

## Star 趋势

[![Star History Chart](https://api.star-history.com/svg?repos=sleep1223/fast-soy-admin&type=Date)](https://star-history.com/#sleep1223/fast-soy-admin&Date)

## 开源协议

项目基于 [MIT © 2024](./LICENSE) 协议，仅供学习参考，商业使用请保留作者版权信息，作者不保证也不承担任何软件的使用风险。