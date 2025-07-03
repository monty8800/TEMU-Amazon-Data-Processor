"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

interface TaskFile {
  name: string;
  path: string;
  size: number;
  modified: string;
}

interface Task {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  files: string[];
  process_type: string;
  result_dir: string | null;
  log_file: string | null;
  error: string | null;
}

export default function TaskPage() {
  const params = useParams();
  const taskId = params.id as string;
  
  const [task, setTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [resultFiles, setResultFiles] = useState<TaskFile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 获取任务状态
  const fetchTaskStatus = async () => {
    try {
      const response = await fetch(`http://localhost:8089/tasks/${taskId}`);
      if (!response.ok) {
        throw new Error('获取任务状态失败');
      }
      const data = await response.json();
      setTask(data);
      
      // 如果任务完成或失败，获取结果文件
      if (data.status === 'completed' || data.status === 'failed') {
        fetchResultFiles();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取任务状态失败');
    }
  };

  // 获取任务日志
  const fetchLogs = async () => {
    try {
      const response = await fetch(`http://localhost:8089/tasks/${taskId}/logs`);
      if (!response.ok) {
        throw new Error('获取日志失败');
      }
      const data = await response.json();
      setLogs(data.logs);
    } catch (err) {
      console.error('获取日志失败:', err);
    }
  };

  // 获取结果文件列表
  const fetchResultFiles = async () => {
    try {
      const response = await fetch(`http://localhost:8089/tasks/${taskId}/files`);
      if (!response.ok) {
        throw new Error('获取结果文件失败');
      }
      const data = await response.json();
      setResultFiles(data.files);
    } catch (err) {
      console.error('获取结果文件失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载
    fetchTaskStatus();
    fetchLogs();

    // 定时刷新任务状态
    const intervalId = setInterval(() => {
      if (task && (task.status === 'pending' || task.status === 'processing')) {
        fetchTaskStatus();
        fetchLogs();
      } else {
        clearInterval(intervalId);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [taskId, task?.status]);

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 获取处理类型文本
  const getProcessTypeText = (type: string): string => {
    switch (type) {
      case '1': return '仅处理亚马逊结算数据';
      case '2': return '仅处理TEMU数据';
      case '3': return '处理所有数据';
      default: return '未知处理类型';
    }
  };

  // 获取状态文本和颜色
  const getStatusInfo = (status: string): { text: string; color: string } => {
    switch (status) {
      case 'pending':
        return { text: '等待处理', color: 'bg-yellow-100 text-yellow-800' };
      case 'processing':
        return { text: '处理中', color: 'bg-blue-100 text-blue-800' };
      case 'completed':
        return { text: '处理完成', color: 'bg-green-100 text-green-800' };
      case 'failed':
        return { text: '处理失败', color: 'bg-red-100 text-red-800' };
      default:
        return { text: '未知状态', color: 'bg-gray-100 text-gray-800' };
    }
  };

  if (loading && !task) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">错误！</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
        <div className="mt-4">
          <Link href="/" className="text-blue-500 hover:underline">
            返回首页
          </Link>
        </div>
      </div>
    );
  }

  const statusInfo = task ? getStatusInfo(task.status) : { text: '', color: '' };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">任务详情</h1>
        <Link href="/" className="text-blue-500 hover:underline">
          返回首页
        </Link>
      </div>

      {task && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-gray-600">任务ID:</p>
              <p className="font-medium">{task.id}</p>
            </div>
            <div>
              <p className="text-gray-600">创建时间:</p>
              <p className="font-medium">{new Date(task.created_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600">处理类型:</p>
              <p className="font-medium">{getProcessTypeText(task.process_type)}</p>
            </div>
            <div>
              <p className="text-gray-600">状态:</p>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                {statusInfo.text}
              </span>
            </div>
          </div>

          {task.error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
              <strong className="font-bold">处理失败：</strong>
              <span className="block sm:inline">{task.error}</span>
            </div>
          )}

          {(task.status === 'pending' || task.status === 'processing') && (
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
              <div className="bg-blue-600 h-2.5 rounded-full animate-pulse w-full"></div>
            </div>
          )}
        </div>
      )}

      {/* 日志显示区域 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">处理日志</h2>
        <div className="bg-gray-100 p-4 rounded-md overflow-auto max-h-60">
          <pre className="text-sm text-gray-800 whitespace-pre-wrap">{logs || '暂无日志'}</pre>
        </div>
      </div>

      {/* 结果文件列表 */}
      {task?.status === 'completed' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">处理结果</h2>
          {resultFiles.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      文件名
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      大小
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      修改时间
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {resultFiles.map((file, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {file.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFileSize(file.size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(file.modified).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <a
                          href={`http://localhost:8089/tasks/${taskId}/download/${encodeURIComponent(file.name)}`}
                          download
                          className="text-blue-600 hover:text-blue-900"
                        >
                          下载
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">暂无处理结果文件</p>
          )}
        </div>
      )}
    </div>
  );
}
