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


<span><a href="./README.zh_CN.md">English</a> | 中文</span>

</div>

> [!NOTE]
> If you think `FastSoyAdmin` is helpful to you, or you like our project, please give us a ⭐️ on GitHub. Your support is the driving force for us to continue to improve and add new features! Thank you for your support!

## Introduction

[`FastSoyAdmin`](https://github.com/sleep1223/fast-soy-admin) is a clean, elegant, beautiful and powerful admin template, based on the latest technology stack, front-end including Vue3, Vite5, TypeScript, Pinia and UnoCSS, back-end including FastAPI、Pydantic and Tortoise ORM. It has built-in rich theme configuration and components, strict code specifications, and an automated file routing system. In addition, it also uses the online mock data solution based on ApiFox. `FastSoyAdmin` provides you with a one-stop admin solution, no additional configuration, and out of the box. It is also a best practice for learning cutting-edge technologies quickly.


## Features

Sure! Here's the translation:

- **Cutting-Edge Technology**: The backend uses the latest tech stack, including FastAPI, Pydantic, Tortoise ORM, while the frontend uses Vue3, Vite5, TypeScript, Pinia, and UnoCSS.
- **Unique Access Control**: The backend features unique access control, with strict separation of user roles and permissions between the frontend and backend.
- **Detailed Log Management**: Based on [`SoybeanAdmin`](https://github.com/sleep1223/fast-soy-admin), it adds log management and API access control features to meet real business needs, enabling secondary verification of backend permissions.
- **Integrated Utility Tools**: The backend includes many useful tools with low code coupling, and some utility functions have been rewritten.
- **Clear project architecture**: using pnpm monorepo architecture, clear structure, elegant and easy to understand.
- **Strict code specifications**: front-end follow the [SoybeanJS specification](https://docs.soybeanjs.cn/standard), integrate eslint, prettier and simple-git-hooks to ensure the code is standardized, back-end use [Ruff](https://docs.astral.sh/ruff/) and [Pyright](https://microsoft.github.io/pyright) to ensure the code is standardized.

- **Rich theme configuration**: built-in a variety of theme configurations, perfectly integrated with UnoCSS.
- **Built-in internationalization solution**: easily realize multi-language support.
- **Rich page components**: built-in a variety of pages and components, including 403, 404, 500 pages, as well as layout components, tag components, theme configuration components, etc.
- **Command line tool**: built-in efficient command line tool, git commit, delete file, release, etc.
- **Mobile adaptation**: perfectly support mobile terminal to realize adaptive layout.



## Related

- [Preview Link](https://fast-soy-admin.sleep0.de/)
- [Project Documentation](https://sleep1223.github.io/fast-soy-admin-docs/zh/)
- [Apifox Documentation](https://apifox.com/apidoc/shared-7cd78102-46eb-4701-88b1-3b49c006504b)
- [GitHub Repository](https://github.com/sleep1223/fast-soy-admin)
- [SoybeanAdmin](https://gitee.com/honghuangdc/soybean-admin)

## Example Images

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


## Usage

Make sure your environment meets the following requirements:

- **git**: you need git to clone and manage project versions.
- **python**: >= 3.10
- **NodeJS**: >=18.0.0, recommended 18.19.0 or higher.
- **pnpm**: >= 8.0.0, recommended 8.14.0 or higher.


**Clone Project**

```bash
git clone https://github.com/sleep1223/fast-soy-admin
```


**Install Dependencies**

```bash
pdm install or poery install
cd web && pnpm i
```

> Since this project uses the pnpm monorepo management method, please do not use npm or yarn to install dependencies.


**Start Project**

front-end
```bash
pnpm dev
```

back-end
```bash
pdm run run.py 或者 poetry run run.py
```


**Build Project**

```bash
pnpm build
```


## How to Contribute

We warmly welcome and appreciate all forms of contributions. If you have any ideas or suggestions, please feel free to share them by submitting [pull requests](https://github.com/sleep1223/fast-soy-admin/pulls) or creating GitHub [issue](https://github.com/sleep1223/fast-soy-admin/issues/new).

## Git Commit Guidelines

This project has built-in `commit` command, you can execute `pnpm commit` to generate commit information that conforms to [Conventional Commits](https://www.conventionalcommits.org/) specification. When submitting PR, please be sure to use `commit` command to create commit information to ensure the standardization of information.


## Browser Support

It is recommended to use the latest version of Chrome in development for a better experience.

| [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/archive/internet-explorer_9-11/internet-explorer_9-11_48x48.png" alt="IE" width="24px" height="24px"  />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/edge/edge_48x48.png" alt=" Edge" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/firefox/firefox_48x48.png" alt="Firefox" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/chrome/chrome_48x48.png" alt="Chrome" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/safari/safari_48x48.png" alt="Safari" width="24px" height="24px" />](http://godban.github.io/browsers-support-badges/) |
| --- | --- | --- | --- | --- |
| not support | last 2 versions | last 2 versions | last 2 versions | last 2 versions |

## OpenSource Author

[Sleep1223](https://github.com/Sleep1223)


## Contributors

Thanks the following people for their contributions. If you want to contribute to this project, please refer to [How to Contribute](#how-to-contribute).

<a href="https://github.com/sleep1223/fast-soy-admin/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=sleep1223/fast-soy-admin" />
</a>

## Communication

`FastSoyAdmin` is a completely open source and free project, helping developers to develop medium and large-scale management systems more conveniently. It also provides QQ communication groups. If you have any questions, please feel free to ask in the group.

![QQ Group](https://raw.githubusercontent.com/sleep1223/fast-soy-admin-docs/51832d41f1d951bd9d61a9bcfdf137deb81fd3c5/src/assets/qqgroup.jpg)

## Star Trend

[![Star History Chart](https://api.star-history.com/svg?repos=sleep1223/fast-soy-admin&type=Date)](https://star-history.com/#sleep1223/fast-soy-admin&Date)

## License

This project is based on the [MIT © 2024](./LICENSE) protocol, for learning purposes only, please retain the author's copyright information for commercial use, the author does not guarantee and is not responsible for the software.