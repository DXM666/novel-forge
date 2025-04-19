import React from 'react';

const MainContent = () => (
  <div className="flex-1 overflow-y-auto bg-white">
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* 标题输入 */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Novel Title"
          className="w-full text-3xl font-bold border-none focus:outline-none focus:ring-0 placeholder-gray-300"
        />
        <input
          type="text"
          placeholder="Subtitle or tagline"
          className="w-full text-xl text-gray-500 border-none focus:outline-none focus:ring-0 placeholder-gray-300 mt-2"
        />
      </div>

      {/* 章节区域 */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Chapter 1: The Beginning</h2>
          <div className="flex space-x-2">
            <button className="p-1 text-gray-500 hover:text-gray-700">
              <i className="fas fa-cog"></i>
            </button>
            <button className="p-1 text-gray-500 hover:text-gray-700">
              <i className="fas fa-trash-alt"></i>
            </button>
          </div>
        </div>

        {/* 编辑内容 */}
        <div className="editor-content">
          {/* 示例段落 */}
          <p className="text-gray-800 mb-4">
            The city slept beneath a blanket of stars, its towering spires reaching toward the
            heavens like the fingers of a giant. Neon lights flickered in the distance, casting
            eerie reflections on the rain-slicked streets.
          </p>
          {/* AI 建议示例 */}
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
            <p className="text-sm text-blue-700">
              <span className="font-semibold">AI Suggestion:</span> Consider adding more sensory
              details about the rain to enhance atmosphere.
            </p>
          </div>
          {/* 继续内容... */}
          {/* TODO: 更多段落和交互元素 */}
        </div>
      </div>

      {/* 新章节按钮 */}
      <div className="border-t border-gray-200 pt-6">
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 flex items-center">
          <i className="fas fa-plus mr-2"></i> Add New Chapter
        </button>
      </div>
    </div>
  </div>
);

export default MainContent;
