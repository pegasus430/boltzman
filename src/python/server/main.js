import { ModuleRegistry } from '@ag-grid-community/core';
import '@ag-grid-community/styles/ag-grid.css';
import '@ag-grid-community/styles/ag-theme-alpine.css';
import { AgGridVue } from '@ag-grid-community/vue3';
import { ColumnsToolPanelModule } from '@ag-grid-enterprise/column-tool-panel';
import { MenuModule } from '@ag-grid-enterprise/menu';
import { ServerSideRowModelModule } from '@ag-grid-enterprise/server-side-row-model';
import { createApp } from 'vue';

// Register the required feature modules with the Grid
ModuleRegistry.registerModules([
  ServerSideRowModelModule,
  MenuModule,
  ColumnsToolPanelModule,
]);

const VueExample = {
  template: `
        <div style="height: 100%">
            <ag-grid-vue
                
                style="width: 100%; height: 100%;"
                class="ag-theme-alpine-dark"
                :columnDefs="columnDefs"
                @grid-ready="onGridReady"
                :defaultColDef="defaultColDef"
                :rowModelType="rowModelType"></ag-grid-vue>
        </div>
    `,
  components: {
    'ag-grid-vue': AgGridVue,
  },
  data: function () {
    return {
      columnDefs: [
        { field: 'athlete', minWidth: 220 },
        { field: 'country', minWidth: 200 },
        { field: 'year' },
        { field: 'sport', minWidth: 200 },
        { field: 'gold' },
        { field: 'silver' },
        { field: 'bronze' },
      ],
      gridApi: null,
      columnApi: null,
      defaultColDef: {
        flex: 1,
        minWidth: 100,
      },
      rowModelType: null,
    };
  },
  created() {
    this.rowModelType = 'serverSide';
  },
  methods: {
    onGridReady(params) {
      this.gridApi = params.api;
      this.gridColumnApi = params.columnApi;

      const updateData = (data) => {
        // setup the fake server with entire dataset
        var fakeServer = createFakeServer(data);
        // create datasource with a reference to the fake server
        var datasource = createServerSideDatasource(fakeServer);
        // register the datasource with the grid
        params.api.setServerSideDatasource(datasource);
      };

      fetch('https://www.ag-grid.com/example-assets/olympic-winners.json')
        .then((resp) => resp.json())
        .then((data) => updateData(data));
    },
  },
};

window.createServerSideDatasource = function createServerSideDatasource(
  server
) {
  return {
    getRows: (params) => {
      console.log('[Datasource] - rows requested by grid: ', params.request);
      // get data for request from our fake server
      var response = server.getData(params.request);
      // simulating real server call with a 500ms delay
      setTimeout(function () {
        if (response.success) {
          // supply rows for requested block to grid
          params.success({ rowData: response.rows });
        } else {
          params.fail();
        }
      }, 500);
    },
  };
};

window.createFakeServer = function createFakeServer(allData) {
  return {
    getData: (request) => {
      // take a copy of the data to return to the client
      var requestedRows = allData.slice();
      return {
        success: true,
        rows: requestedRows,
      };
    },
  };
};

createApp(VueExample).mount('#app');
