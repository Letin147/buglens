export default function Bug1() {
  return (
    <div>
      <nav className="navbar">
        <span className="logo">DemoShop</span>
        <div className="nav-links">
          <span>首页</span>
          <span>分类</span>
          <span>购物车(2)</span>
          <span>我的订单</span>
        </div>
      </nav>
      <main className="bug1-page">
        <section className="checkout-card">
          <button type="button" className="btn-primary">
            提交订单
          </button>
          <h1>订单结算</h1>
          <div className="checkout-row">
            <span>无线降噪耳机 Pro</span>
            <span>¥899.00</span>
          </div>
          <div className="checkout-row">
            <span>运输保价服务</span>
            <span>¥19.90</span>
          </div>
          <div className="checkout-row">
            <span>运费（顺丰速运）</span>
            <span>¥12.00</span>
          </div>
          <div className="checkout-row">
            <span>合计</span>
            <span className="checkout-total">¥930.90</span>
          </div>
        </section>
      </main>
    </div>
  );
}
