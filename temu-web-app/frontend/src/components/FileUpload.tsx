"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function FileUpload() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [processType, setProcessType] = useState<string>("3");
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(e.target.files);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!files || files.length === 0) {
      setError("请选择至少一个文件");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      
      // 添加所有文件到表单
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      
      // 添加处理类型
      formData.append('process_type', processType);

      // 发送请求到后端
      const response = await fetch('http://localhost:8089/upload/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '上传失败');
      }

      const data = await response.json();
      
      // 上传成功后跳转到任务详情页
      router.push(`/tasks/${data.task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传过程中发生错误');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">TEMU & Amazon 数据处理系统</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            选择处理类型
          </label>
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                type="radio"
                id="amazon"
                name="processType"
                value="1"
                checked={processType === "1"}
                onChange={() => setProcessType("1")}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="amazon" className="ml-2 block text-sm text-gray-700">
                仅处理亚马逊结算数据
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                type="radio"
                id="temu"
                name="processType"
                value="2"
                checked={processType === "2"}
                onChange={() => setProcessType("2")}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="temu" className="ml-2 block text-sm text-gray-700">
                仅处理TEMU数据
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                type="radio"
                id="both"
                name="processType"
                value="3"
                checked={processType === "3"}
                onChange={() => setProcessType("3")}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="both" className="ml-2 block text-sm text-gray-700">
                处理所有数据
              </label>
            </div>
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            上传文件
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
            <div className="space-y-1 text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
                aria-hidden="true"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="flex text-sm text-gray-600">
                <label
                  htmlFor="file-upload"
                  className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                >
                  <span>上传文件</span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    multiple
                    className="sr-only"
                    onChange={handleFileChange}
                    accept=".xlsx,.xls,.csv,.zip,.rar,.7z"
                  />
                </label>
                <p className="pl-1">或拖放文件到此处</p>
              </div>
              <p className="text-xs text-gray-500">支持 Excel、CSV 和压缩文件 (ZIP、RAR、7Z)</p>
              {files && files.length > 0 && (
                <p className="text-sm text-green-600">已选择 {files.length} 个文件</p>
              )}
            </div>
          </div>
        </div>
        
        {error && (
          <div className="text-red-500 text-sm">{error}</div>
        )}
        
        <div>
          <button
            type="submit"
            disabled={uploading}
            className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              uploading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {uploading ? '处理中...' : '开始处理'}
          </button>
        </div>
      </form>
    </div>
  );
}
