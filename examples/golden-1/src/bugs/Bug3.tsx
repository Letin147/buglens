export default function Bug3() {
  return (
    <main className="bug3-page">
      <h1>会员套餐</h1>
      <div className="pricing-grid">
        <section className="price-card">
          <div className="plan">基础版</div>
          <div className="amount">¥19</div>
          <ul>
            <li>每月 3 次专属客服</li>
            <li>基础数据报表</li>
            <li>1 个协作席位</li>
          </ul>
        </section>
        <section className="price-card popular" style={{ marginTop: 56 }}>
          <div className="plan">专业版</div>
          <div className="amount">¥49</div>
          <ul>
            <li>不限次专属客服</li>
            <li>高级数据报表</li>
            <li>5 个协作席位</li>
            <li>API 访问</li>
          </ul>
        </section>
        <section className="price-card">
          <div className="plan">企业版</div>
          <div className="amount">¥199</div>
          <ul>
            <li>7×24 专属客服</li>
            <li>定制数据报表</li>
            <li>不限席位</li>
            <li>私有化部署</li>
          </ul>
        </section>
      </div>
    </main>
  );
}
