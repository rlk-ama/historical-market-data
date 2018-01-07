function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

var app = new Vue({
  delimiters:['${', '}'],
  el: '#overview',
  data: {
    marketUpdate: 'Click to update market data',
    markets: []
  },
  beforeMount(){
    axios.get('/markets')
      .then(response => {
        this.markets = response.data.markets
        })
      .catch(error => { })
  }, 
  methods: {
    updateMarkets: function () {
      this.marketUpdate = 'Updating markets, please wait';
      axios.get('/download')
      .then(response => {
        this.marketUpdate = 'Markets updated!';
        axios.get('/markets')
        .then(response => {
          this.markets = response.data.markets
        })
        .catch(error => { })
        sleep(1000).then(() => {
          this.marketUpdate = 'Click to update market data'
        })
      })
      .catch(error => {
          this.marketUpdate = 'Could not update data, retry later';
          sleep(1000).then(() => {
            this.marketUpdate = 'Click to update market data'
          })
       });
    }
  }
})
