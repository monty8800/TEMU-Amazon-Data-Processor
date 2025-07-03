import FileUpload from '@/components/FileUpload';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            TEMU & Amazon 数据处理系统
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            上传您的数据文件，系统将自动处理并生成结果
          </p>
        </div>

        <div className="mt-10">
          <FileUpload />
        </div>

        <div className="mt-12 text-center">
          <Link href="/tasks" className="text-blue-600 hover:text-blue-800 font-medium">
            查看所有任务 →
          </Link>
        </div>

        <div className="mt-16 border-t border-gray-200 pt-8">
          <div className="text-center text-sm text-gray-500">
            <p>© 2025 TEMU & Amazon 数据处理系统</p>
          </div>
        </div>
      </div>
    </div>
  );
}
