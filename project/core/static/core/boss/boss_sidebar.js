// Only boss screens load this script. Use the cropped PNG's natural proportions.
const bossColumns = document.querySelector('.columns.boss-screen');
const bossSidebar = bossColumns?.querySelector('.boss-sidebar');

if (bossSidebar) {
  const updateWidthCap = () => {
    const cap = `${bossSidebar.getBoundingClientRect().height * 1019 / 1419}px`;
    if (bossColumns.style.getPropertyValue('--boss-sidebar-max-width') !== cap) {
      bossColumns.style.setProperty('--boss-sidebar-max-width', cap);
    }
  };
  updateWidthCap();
  new ResizeObserver(updateWidthCap).observe(bossSidebar);
}
