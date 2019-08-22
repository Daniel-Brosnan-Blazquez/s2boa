#include <stdio.h>
#include <getopt.h>
#include <string.h>
#include <stdlib.h>
#include <explorer_visibility.h>
#include <explorer_data_handling.h>
#include <explorer_orbit.h>
#include <explorer_lib.h>


#define XO_MAX_STR_LENGTH        256

#define MAX_OUT_LEN 511		/* truncate any string longer than this */


int main(int argc, char *argv[])
{
    char *orbit_files;
    char **orbit_files_arr;
    char *sdf_file_input;
    double start_time ;
    double stop_time ;
    double step ;
    long n_times=0;
    long c,i,j; 
    int err; 
    if (argc != 11 )
        {
            printf("Usage: %s -b start_time -e stop_time -o orbit_files -s swath_file [-t step | -n number_of_parts ] \n", argv[0]);
            exit(1);
        }
    else
        {
            while ((c = getopt (argc, argv, ":b:e:o:s:t:n:")) != -1)
                switch (c)
                    {
                    case 'b':
                        start_time = atof(optarg);
                        break;		
                    case 'e':
                        stop_time = atof(optarg);
                        break;		
                    case 'o':
                        orbit_files = optarg;
                        break;		
                    case 't':
                        step = atof(optarg);
                        break;		
                    case 'n':
                        n_times = atof(optarg);
                        break;		
                    case 's':
                        sdf_file_input = optarg;
                        break;	
                    default:
                        break;	
                    }
	

	
            orbit_files_arr = (char **) calloc(2,sizeof(char*));

            char *token="";
            token = strtok(orbit_files, " ");

            j=0;
            while (token != NULL)
                {
                    orbit_files_arr[j]     = (char *) calloc(MAX_OUT_LEN+1,sizeof(char));

                    strncpy(orbit_files_arr[j], token, MAX_OUT_LEN);

                    token = strtok (NULL, " ");
                    j++;
                }

            double duration;
            duration = stop_time - start_time;

            double step_mjd;

            if (n_times != 0) 
		{
                    step_mjd = duration / (n_times -1 );
                    double time_jd[n_times];
                    for (i=0; i<n_times; i++)
			{
                            time_jd[i] = i * step_mjd + start_time;
                            /*printf("Time array: %f\n", time_jd[i]);*/
			}
                    time_jd[n_times - 1] = stop_time;

                    double out_lat[n_times*2];
                    double out_long[n_times*2];
		
                    err = call_eop_cfi( time_jd, n_times, orbit_files_arr, sdf_file_input, 2, 1 , out_lat, out_long);
                    if ( err < 0 ) {
                        return  err;
                    }

                    for (i=0; i<n_times*2; i++) printf("%f,%f ",out_long[i], out_lat[i]);
		
                    printf("\n");
		
		}
            else {	
		step_mjd =  step /86400.0;
		if (duration <=  step_mjd)
                    {	
		        double time_jd[2]; 
	      		time_jd[0] = start_time;
			time_jd[1] = stop_time;
			n_times =2;
			double out_lat[n_times*2];
			double out_long[n_times*2];
		
			err = call_eop_cfi( time_jd, n_times, orbit_files_arr, sdf_file_input, 2, 1 , out_lat, out_long);
			if ( err < 0 ) {
                            return  err;
			}

			for (i=0; i<n_times*2; i++) printf("%f,%f ",out_long[i], out_lat[i]);
		
			printf("\n");
                    } else 
                    {
			n_times = duration / step_mjd +1;
		        double time_jd[n_times];
			for (i=0; i<n_times; i++)
                            {
				time_jd[i] = i * step_mjd + start_time;
				/*printf("Time array: %f\n", time_jd[i]);*/
                            }
			time_jd[n_times - 1] = stop_time;

			double out_lat[n_times*2];
			double out_long[n_times*2];
		
			err = call_eop_cfi( time_jd, n_times, orbit_files_arr, sdf_file_input, 2, 1 , out_lat, out_long);
			if ( err < 0 ) {
                            return  err;
			}

			for (i=0; i<n_times*2; i++) printf("%f,%f ",out_long[i], out_lat[i]);
		
			printf("\n");
		
                    }
            }
        }
    return 0;
}




/* Main program */
/* ------------ */

int call_eop_cfi(double *in_times, long in_n_times, char **in_orbit_files,  char *in_sdf_file, long in_n_orbit_files, long in_orbit_type,  double *out_lat_swath, double *out_lon_swath)

/*
 * input:
 *	in_times	- Pointer to array of double values for TAI time 			[JD2000]
 *	in_n_times	- Long scalar of number of time doubles pointed at by the pointer in_times.
 *	in_orbit_files 	- Pointer to array of string values for orbit filenames
 *	in_n_orbit_files- Long scalar of numbers of orbit file strings pointed at by the pointer in_orbit_files.
 *	in_orbit_type	- Long scalar defining the kind of orbit_files used (see below).
 *	geo_flag	- Long scalar Flag to enable the output of the geolocation parameters (latitude/longitude/altitude)

 *
 * output:
 *	out_lat		- Pointer to array of double values for the latitude			[0   =< degress  < +360]
 *	out_lon		- Pointer to array of double values for the longitude			[-90 =< degress =< +90]
 */


{

  
    /*  Check the size of the array passed in. n should be > 0.*/
    if (in_n_orbit_files < 1) return(-1);
  

  
    /* Earth Explorer Ids.: They should be initialized to NULL allways!!!! */
    xl_time_id     time_id     = {NULL}; 
    xo_orbit_id    orbit_id    = {NULL};
    xl_model_id  	 model_id    = {NULL};
  
    xl_time_id_init_data  time_id_init_data;
    xo_orbit_id_init_data orbit_id_init_data;
    xd_eocfi_file         eocfi_file_array[4];
  
    xd_osf_file osf_data;
 
    /* Accessors data */
    long num_rec; 
    xo_osf_records *osf;
    xo_validity_time val_time;

    xo_propag_id_data   propag_data;
    xo_interpol_id_data interpol_data;

    xo_geo_orbit_init_data geo_init_data;
  
    long i, j;
  
    /* error handling */
    long status;
    long local_status;
    long ierr[XO_ERR_VECTOR_MAX_LENGTH];
    long xv_ierr[XV_ERR_VECTOR_MAX_LENGTH];
    long xd_ierr[XD_ERR_VECTOR_MAX_LENGTH];
    long   n = 0;
    long func_id;
    long code[XO_MAX_COD];          	/* Error codes vector */

    char msg[XO_MAX_COD][XO_MAX_STR];     /* Error messages vector */

    /* common variables */
    long sat_id 		= XO_SAT_SENTINEL_2A;
    long sat_id_geo 	= XO_SAT_GENERIC_GEO;
    long propag_model 	= XO_PROPAG_MODEL_MEAN_KEPL;
    long time_ref_utc 	= XO_TIME_UTC, time_ref_ut1 = XO_TIME_UT1, time_ref_tai = XO_TIME_TAI;

    double pos[3];
    double vel[3];
    double acc[3];

    double pos_ini[3];
    double vel_ini[3];

    double time0,
        time,
        val_time0,
        val_time1;

    long time_init_mode;

    long time_model;

    double inclination;

    double latitude,
        longitude,
        altitude,
        elapsed_anx;

    long orbit0, orbit1, n_files, num, i_loop;
 
    double time1;

    /* variables for xo_osv_compute_extra */

    long extra_choice;
    double orbit_model_out[XO_ORBIT_EXTRA_NUM_DEP_ELEMENTS], 
        orbit_extra_out[XO_ORBIT_EXTRA_NUM_INDEP_ELEMENTS];

    /* xo_time_to_orbit & xo_orbit_to_time variables */

    long orbit_t, second_t, microsec_t;
    double time_t;
    char orbit_scenario_file_t[XO_MAX_STR_LENGTH];
    long time_ref;

    /* variables for xo_orbit_info_from_... */
  
    long abs_orbit;

    /* Other variables */
  
    double time_since_anx ;

    /* xl_time_ref_init_file */
    long   trif_time_model, trif_n_files, trif_time_init_mode, trif_time_ref ;
    double trif_time0, trif_time1, trif_val_time0, trif_val_time1;
    long   trif_orbit0, trif_orbit1;


    /* xl_time_ref_init variable declaration */
    /* ------------------------------------- */
    long tri_sat_id, tri_orbit_num;
    double tri_anx_time, tri_orbit_duration;
    double tri_time[XL_TIME_TRANS_DIM_MAX];
    long tri_ierr[XL_NUM_ERR_TIME_REF_INIT];

    /* orbit initilization */
    /* ------------------- */
    long time_mode, orbit_mode;
    char* files[1];
  
    char **trif_time_files;
    char **input_files;

    /* Variables to call xv_gen_swath */
    /* ------------------------------ */
    xp_atmos_id atmos_id = {NULL};
    char  sdf_name[XV_MAX_STR];/*, stf_name[XV_MAX_STR];*/
    long req_orbit;
    xd_stf_file stf_name;
    xd_sdf_file sdf_data;



    /* Variables to call xv_swath_id_init */
    /* ---------------------------------- */
    xv_swath_id                     swath_id = {NULL};
    xv_swath_info                   swath_info;


    /* Variables to call xv_swathpos_compute */
    /* ------------------------------------- */
    xv_time     swathpos_time;
    xv_swath_point_list swath_point = {0, NULL};

    /* Set error handling mode to SILENT  */
    /* ---------------------------------- */

    xl_silent();
    xo_silent();
    xv_silent();
   
    /*
      xl_verbose();
      xo_verbose();
      xv_verbose();
    */ 



    /* Time Initialization */
    /* ------------------- */

    trif_time_ref       	= XL_TIME_UTC;
    propag_model = XO_PROPAG_MODEL_MEAN_KEPL + XO_PROPAG_MODEL_AUTO;	 
	
	
   
   
    trif_time_model	= XL_TIMEMOD_FOS_PREDICTED; 
    orbit_mode = XO_ORBIT_INIT_AUTO; /*no seria XO_ORBIT_INIT_POF_MODE ??*/
  
  
   
    trif_time_init_mode 	= XL_SEL_FILE;
   
    trif_n_files 	= in_n_orbit_files;
   
    trif_time_files	= (char **) calloc(trif_n_files,sizeof(char*));
   

    /* 
       for(i=0; i < trif_n_files ; i++) {
       printf("\n input time files: %s \n", in_orbit_files[i]);
       }
    */
    status = xl_time_ref_init_file(&trif_time_model, &trif_n_files, in_orbit_files,
                                   &trif_time_init_mode, &trif_time_ref, &trif_time0, &trif_time1,
                                   &trif_orbit0, &trif_orbit1, &trif_val_time0, &trif_val_time1, 
                                   &time_id, ierr);
    if (status != XO_OK)
        {
            func_id = XL_TIME_REF_INIT_FILE_ID;
            xo_get_msg(&func_id, ierr, &n, msg);
            xl_print_msg(&n, msg);
            if (status <= XO_ERR) return(XO_ERR); 
        }



    /* Orbit initialization */
    /* -------------------- */

    time_init_mode = XO_SEL_FILE;

     
    n_files 	  = in_n_orbit_files;
   
    input_files	  =(char **) calloc(n_files,sizeof(char*));

    for(i=0; i < n_files ; i++) {
   
        input_files[i]	= (char *) calloc(MAX_OUT_LEN+1,sizeof(char));
        strncpy(input_files[i], in_orbit_files[i], MAX_OUT_LEN);
        //fprintf(stdout, input_files[i]);
    }

    status =  xo_orbit_init_file(&sat_id, &model_id, &time_id,
                                 &orbit_mode, &n_files, input_files,
                                 &time_init_mode, &time_ref_utc,
                                 &time0, &time1, &orbit0, &orbit1,
                                 &val_time0, &val_time1, &orbit_id,
                                 ierr);

    if (status != XO_OK)
        {
            func_id = XO_ORBIT_INIT_FILE_ID;
            xo_get_msg(&func_id, ierr, &n, msg);
            xo_print_msg(&n, msg);
            if (status <= XO_ERR) return(XO_ERR); 
            /*return -1;*/
        }

    status = xo_orbit_get_propag_config(&orbit_id, &propag_data); 

    /*   val_time0 = propag_data.propag_osv.val_time.start;
         val_time1 = propag_data.propag_osv.val_time.stop;
  

 

         /*-----------------------------------*
         *          XV_GEN_SWATH             *
         *-----------------------------------*/

    /*sdf_file     =(char **) calloc(1,sizeof(char*));
      sdf_file[0]	= (char *) calloc(MAX_OUT_LEN+1,sizeof(char));
      strcpy(sdf_file[0], in_sdf_file);
    
      fprintf(stdout, sdf_file[0]);*/ 


    req_orbit=propag_data.propag_osv.abs_orbit;
   
    strcpy(sdf_name,in_sdf_file);
    status = xd_read_sdf (sdf_name, &sdf_data, xd_ierr);
    if (local_status != XV_OK)
        {
            func_id = XD_READ_SDF_ID;
            xd_get_msg(&func_id, xd_ierr, &n, msg);
            xv_print_msg(&n, msg);
            if (status <= XV_ERR) return(XV_ERR); 
        }



    status = xv_gen_swath_no_file(&orbit_id, &atmos_id,
                                  &req_orbit, &sdf_data, 
                                  &stf_name,
                                  xv_ierr);
    xd_free_sdf(&sdf_data);
    if (status != XV_OK)
        {
            func_id = XV_GEN_SWATH_ID;
            xv_get_msg(&func_id, xv_ierr, &n, msg);
            xv_print_msg(&n, msg);
            if (status <= XV_ERR) return(XV_ERR); 
        }

    /*
      printf("\n\n\nXV_SWATH_ID_INIT\n");    */ 
    swath_info.sdf_file = NULL;
    swath_info.stf_file = &stf_name;
    swath_info.nof_regen_orbits = 0;
    swath_info.filename = NULL;
    swath_info.type = XV_STF_DATA;
   
    local_status = xv_swath_id_init(&swath_info, &atmos_id,
                                    &swath_id, xv_ierr);

    if (local_status != XV_OK)
        {
            func_id = XV_SWATH_ID_INIT_ID;
            xv_get_msg(&func_id, xv_ierr, &n, msg);
            xv_print_msg(&n, msg);
            if (status <= XV_ERR) return(XV_ERR); 
        }



    num = in_n_times;
 
 

    for (i_loop = 0; i_loop < num; i_loop++)
        {

            time = in_times[i_loop];


            status = xo_osv_compute(&orbit_id, &propag_model, &time_ref_utc, &time,
                                    /* outputs */
                                    pos, vel, acc, ierr);

            if (status != XO_OK)
                {
                    func_id = XO_OSV_COMPUTE_ID;
                    xo_get_msg(&func_id, ierr, &n, msg);
                    xo_print_msg(&n, msg);
                    if (status <= XO_ERR) return(XO_ERR); 
                }

            /*
              fprintf(stdout, "\n\t-    time = %lf", time );
              fprintf(stdout, "\n\t-  pos[0] = %lf", pos[0] );
              fprintf(stdout, "\n\t-  pos[1] = %lf", pos[1] );
              fprintf(stdout, "\n\t-  pos[2] = %lf", pos[2] );
              fprintf(stdout, "\n\t-  vel[0] = %lf", vel[0] );
              fprintf(stdout, "\n\t-  vel[1] = %lf", vel[1] );
              fprintf(stdout, "\n\t-  vel[2] = %lf", vel[2] );
              fprintf(stdout, "\n\t-  acc[0] = %lf", acc[0] );
              fprintf(stdout, "\n\t-  acc[1] = %lf", acc[1] );
              fprintf(stdout, "\n\t-  acc[2] = %lf", acc[2] );
            */
 
            /* Latitude / Longitude / Altitude */

            extra_choice = XO_ORBIT_EXTRA_GEOLOCATION + XO_ORBIT_EXTRA_DEP_ANX_TIMING;
     
            status = xo_osv_compute_extra(&orbit_id, &extra_choice, 
                                          orbit_model_out, orbit_extra_out, ierr);
            if (status != XO_OK)
                {
                    func_id = XO_OSV_COMPUTE_EXTRA_ID;
                    xo_get_msg(&func_id, ierr, &n, msg);
                    xo_print_msg(&n, msg);
                    if (status <= XO_ERR) return(XO_ERR); 
                }


            latitude		= orbit_extra_out[XO_ORBIT_EXTRA_GEOD_LAT];
            longitude		= orbit_extra_out[XO_ORBIT_EXTRA_GEOC_LONG];
            time_since_anx 	= orbit_model_out[XO_ORBIT_EXTRA_DEP_SEC_SINCE_ANX];
            abs_orbit      	= orbit_model_out[XO_ORBIT_EXTRA_DEP_ORBIT_NUMBER];


            float fracpart =time_since_anx -(long)time_since_anx;
            float msec_time_since_anx = fracpart *1E6;

            /* --------------------- */
            /*   XV_SWATHPOS_COMPUTE */
            /* --------------------- */
            swathpos_time.type = XV_ORBIT_TYPE;
            swathpos_time.orbit_type = XV_ORBIT_ABS;
            swathpos_time.orbit_num = abs_orbit;
            swathpos_time.sec = time_since_anx;
            swathpos_time.msec = msec_time_since_anx;


            status = xv_swathpos_compute(&orbit_id, &swath_id, &swathpos_time,
                                         &swath_point, ierr);

            if (local_status != XV_OK)
                {
                    func_id = XV_SWATHPOS_COMPUTE_ID;
                    xv_get_msg(&func_id, ierr, &n, msg);
                    xv_print_msg(&n, msg);
                    if (status <= XV_ERR) return(XV_ERR); 
                }
  
  
            /* print outputs * /
               printf("\n\nInputs: ");   
               printf("\n   Absolute Orbit: %d", swathpos_time.orbit_num);   
               printf("\n   ANX Time: %f", swathpos_time.sec+(swathpos_time.msec*1.e-6));
               printf("\nOutputs: ");   
               printf("\n   Swath longitude 1: %f", swath_point.swath_point[0].lon);   
               printf("\n   Swath latitude 1: %f", swath_point.swath_point[0].lat);
            */

            int index_i_loop =  num*2  - i_loop-1;

            if (swath_point.num_rec > 0){
                out_lat_swath[i_loop] 	= swath_point.swath_point[0].lat;
                out_lon_swath[i_loop] 	= swath_point.swath_point[0].lon;
                
                out_lat_swath[index_i_loop] 	= swath_point.swath_point[2].lat;
                out_lon_swath[index_i_loop] 	= swath_point.swath_point[2].lon;
            }
            else{
                return (-1);
            }

            /*
              fprintf(stdout, "\n\t-  latitude Side1 = %lf", out_lat_swath[i_loop] );
              fprintf(stdout, "\n\t-  longitude Side1 = %lf", out_lon_swath[i_loop] );
              
              fprintf(stdout, "\n\t-  latitude  Side2 = %lf", out_lat_swath[index_i_loop] );
              fprintf(stdout, "\n\t-  longitude Side2 = %lf", out_lon_swath[index_i_loop] );
              
              fprintf(stdout, "\n\t-  elapsed_anx  = %lf", time_since_anx );
            */
            
        }

	
	
    status = xo_orbit_close(&orbit_id, ierr);
    if (status != XO_OK)
        {
            func_id = XO_ORBIT_CLOSE_ID;
            xo_get_msg(&func_id, ierr, &n, msg);
            xo_print_msg(&n, msg);
            if (status <= XO_ERR) return(XO_ERR); 
        }

    xl_time_close(&time_id, ierr);

    free (trif_time_files);
    free (input_files);

    /*  return(1);*/
   
}


#undef MAX_OUT_LEN
   
#undef XO_MAX_STR_LENGTH

