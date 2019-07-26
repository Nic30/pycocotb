module I2c_wire (
		output i_scl_i,
        input i_scl_o,
        input i_scl_t,

        output i_sda_i,
        input i_sda_o,
        input i_sda_t,

        input o_scl_i,
        output o_scl_o,
        output o_scl_t,

        input o_sda_i,
        output o_sda_o,
        output o_sda_t
    );

    assign i_scl_i = o_scl_i;
    assign i_sda_i = o_sda_i;
    assign o_scl_o = i_scl_o;
    assign o_scl_t = i_scl_t;
    assign o_sda_o = i_sda_o;
    assign o_sda_t = i_sda_t;
endmodule