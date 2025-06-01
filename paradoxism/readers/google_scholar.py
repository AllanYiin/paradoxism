import os
import re
import requests
from tqdm import tqdm
from scholarly import scholarly
from datetime import datetime
import logging

class GoogleScholarReader:
    def __init__(self, base_path=None):
        """初始化，確認基礎路徑存在，若不存在則創建"""
        if base_path is None:
            base_path = os.path.join(os.path.expanduser('~'),".paradoxism", "scholar_results")
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def save_results_to_file(self, query, results):
        """將查詢結果儲存至 txt 檔案"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.base_path, f"{query}_{timestamp}.txt")

            with open(filename, "w", encoding="utf-8") as file:
                for result in results:
                    file.write(f"Title: {result['title']}\n")
                    file.write(f"URL: {result['url']}\n\n")

            logging.info("查詢結果已儲存至 %s", filename)
        except Exception as e:
            logging.error("儲存查詢結果失敗: %s", e)

    def get_pdf_url(self, url):
        """
        根據提供的 URL 轉換成相應的 PDF 下載連結。
        """
        # arXiv 轉換邏輯
        arxiv_pattern = r"https://arxiv.org/abs/(\d+\.\d+)"
        ieee_pattern = r"https://ieeexplore.ieee.org/abstract/document/(\d+)"
        acl_pattern = r"https://aclanthology.org/(.+)/$"  # ACL Anthology 規則
        neurips_pattern = r"https://proceedings.neurips.cc/paper_files/paper/\d+/hash/([a-f0-9]+)-Abstract-Conference.html"  # NeurIPS 規則
        cvpr_pattern = r"https://openaccess.thecvf.com/content/.+/html/(.+)_paper.html"  # CVPR 規則
        openreview_pattern = r"https://openreview.net/forum\?id=(.+)"  # OpenReview 規則
        wiley_pattern = r"https://onlinelibrary.wiley.com/doi/(abs|epdf)/(.+)"  # Wiley 規則

        # 匹配 arXiv 的 URL 並轉換為 PDF 下載鏈接
        arxiv_match = re.match(arxiv_pattern, url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            return f"https://arxiv.org/pdf/{arxiv_id}"

        # 匹配 IEEE Xplore 的 URL 並轉換為 PDF 下載鏈接
        ieee_match = re.match(ieee_pattern, url)
        if ieee_match:
            ieee_id = ieee_match.group(1)
            return f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={ieee_id}"

        # 匹配 ACL Anthology 的 URL 並轉換為 PDF 下載鏈接
        acl_match = re.match(acl_pattern, url)
        if acl_match:
            acl_id = acl_match.group(1)
            return f"https://aclanthology.org/{acl_id}.pdf"

        # 匹配 NeurIPS 的 URL 並轉換為 PDF 下載鏈接
        neurips_match = re.match(neurips_pattern, url)
        if neurips_match:
            neurips_id = neurips_match.group(1)
            return f"https://proceedings.neurips.cc/paper_files/paper/2023/file/{neurips_id}-Paper-Conference.pdf"

        # 匹配 CVPR 的 URL 並轉換為 PDF 下載鏈接
        cvpr_match = re.match(cvpr_pattern, url)
        if cvpr_match:
            cvpr_id = cvpr_match.group(1)
            return f"https://openaccess.thecvf.com/content/CVPR2024/papers/{cvpr_id}_paper.pdf"

        # 匹配 OpenReview 的 URL 並轉換為 PDF 下載鏈接
        openreview_match = re.match(openreview_pattern, url)
        if openreview_match:
            openreview_id = openreview_match.group(1)
            return f"https://openreview.net/pdf?id={openreview_id}"

        # 匹配 Wiley 的 URL 並轉換為 PDF 下載鏈接
        wiley_match = re.match(wiley_pattern, url)
        if wiley_match:
            wiley_id = wiley_match.group(2)
            return f"https://onlinelibrary.wiley.com/doi/epdf/{wiley_id}"

        # 如果不匹配已知的模式，返回原始 URL
        return url
    def download_paper(self, title, url, save_path=None):
        """下載 PDF 論文"""

        sanitized_title = "".join([c for c in title if c.isalnum() or c in " _-"]).rstrip().replace(' ','_').replace('-', '_')
        file_path = os.path.join(save_path, f"{sanitized_title}.pdf")
        if not os.path.exists(file_path):
            try:
                response = requests.get(url)
                if response.headers.get("content-type") == "application/pdf":
                    response.raise_for_status()
                    save_path=self.base_path if not save_path else save_path

                    # 以論文標題作為檔名下載 PDF
                    with open(file_path, "wb") as file:
                        file.write(response.content)
                        logging.info("PDF下載成功: %s: %s", title, url)
                else:
                    content_type = response.headers.get("content-type")
                    logging.error("無法下載 %s: %s", title, content_type)
            except requests.exceptions.RequestException as e:
                logging.error("無法下載 %s: %s", title, e)
            except Exception as e:
                logging.error("寫入文件失敗: %s", e)

    def search_and_download(self, query):
        """查詢 Google Scholar 並下載結果的 PDF 檔案"""
        try:
            search_query = scholarly.search_pubs(query)
            save_path=os.path.join(self.base_path,query)
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            results = []

            for paper in tqdm(search_query):
                title = paper['bib']['title']
                url = paper.get('pub_url', None)
                url = self.get_pdf_url(url)

                logging.info("論文標題: %s", title)

                if url:
                    self.download_paper(title, url,save_path)

                results.append({
                    'title': title,
                    'url': url if url else "無下載連結"
                })

            self.save_results_to_file(query, results)
        except Exception as e:
            logging.error("查詢失敗: %s", e)
