"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Task {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  process_type: string;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await fetch('http://localhost:8089/tasks');
        if (!response.ok) {
          throw new Error('获取任务列表失败');
        }
        const data = await response.json();
        setTasks(data.tasks || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取任务列表失败');
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

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

  if (loading) {
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

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">任务列表</h1>
        <Link href="/" className="text-blue-500 hover:underline">
          返回首页
        </Link>
      </div>

      {tasks.length > 0 ? (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  任务ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  创建时间
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  处理类型
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tasks.map((task) => {
                const statusInfo = getStatusInfo(task.status);
                return (
                  <tr key={task.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {task.id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(task.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getProcessTypeText(task.process_type)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                        {statusInfo.text}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link href={`/tasks/${task.id}`} className="text-blue-600 hover:text-blue-900">
                        查看详情
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <p className="text-gray-500">暂无任务记录</p>
          <Link href="/" className="mt-4 inline-block text-blue-500 hover:underline">
            创建新任务
          </Link>
        </div>
      )}
    </div>
  );
}
